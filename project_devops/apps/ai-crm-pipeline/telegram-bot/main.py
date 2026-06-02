import os
import logging
import json
import uuid
from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import redis.asyncio as redis

from agents import AgentRole, get_agent
from llm_gemini import normalize_extraction
from compliance_guard import evaluate_reply

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_CRM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", ""))
REDIS_URL = os.getenv("REDIS_URL", "redis://platform-redis:6379/0")
QUEUE_KEY = os.getenv("CRM_QUEUE_KEY", "crm:queue:messages")

# Agent 4: auto-reply | Agent 5: analyze → CRM queue (worker + Odoo agent 3)
reply_agent = get_agent(AgentRole.TELEGRAM_REPLY)
analyze_agent = get_agent(AgentRole.TELEGRAM_ANALYZE)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Xin chào {user.mention_html()}! Tôi là trợ lý BĐS TNT. "
        rf"Hỏi về căn hộ, nhà phố, đất nền — tôi hỗ trợ ngay!",
        reply_markup=ForceReply(selective=True),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    user = update.effective_user
    chat_id = update.effective_chat.id
    message_id = f"tg-{chat_id}-{update.message.message_id}"
    timestamp = update.message.date.isoformat() if update.message.date else None

    logger.info("Telegram msg from %s: %s", user.id, message_text[:80])

    # --- Agent 4: tự động phản hồi khách ---
    reply = "Cảm ơn bạn đã liên hệ! Team TNT sẽ phản hồi sớm."
    try:
        reply_prompt = [
        {
            "role": "system",
            "content": (
                "Bạn là một trợ lý bất động sản thân thiện và chuyên nghiệp của TNT. "
                "Trả lời ngắn gọn bằng tiếng Việt (tối đa 2-3 câu). Nếu có thể, đề nghị đặt lịch xem nhà."
            ),
        },
        {"role": "user", "content": message_text},
    ]
        reply = reply_agent.chat_text(messages=reply_prompt)
        decision = evaluate_reply(raw_text=message_text, draft_reply=reply, extracted=None)
        safe_reply = decision.get("rewritten_reply") or reply
        await update.message.reply_text(safe_reply)
        reply = safe_reply
    except Exception as e:
        logger.error("Agent 4 reply failed: %s", e)
        await update.message.reply_text(reply)

    # --- Agent 5: đánh giá hội thoại → queue CRM (worker + Odoo) ---
    try:
        history = context.user_data.get("chat_history", [])
        # Add user message
        history.append({
            "role": "user", 
            "content": message_text,
            "timestamp": timestamp,
            "id": str(update.message.message_id)
        })
        # Add assistant reply
        history.append({
            "role": "assistant", 
            "content": reply,
            "timestamp": timestamp,
            "id": f"assistant-{update.message.message_id}"
        })
        context.user_data["chat_history"] = history[-20:]  # Keep last 20 messages (10 exchanges)

        convo = "\n".join(
            f"{m['role']}: {m['content']}" for m in history[-12:]
        )
        analysis_prompt = [
        {
            "role": "system",
            "content": (
                "Phân tích cuộc trò chuyện khách hàng bất động sản này. Trả về CHỈ JSON hợp lệ: "
                '{"customer_name":string|null,"phone":string|null,'
                '"property_type":"apartment"|"house"|"land"|"commercial"|"other",'
                '"location":string|null,"intent":"purchase"|"inquiry"|"complaint"|"other",'
                '"urgency":"low"|"medium"|"high"|"critical",'
                '"sentiment":"positive"|"neutral"|"negative",'
                '"language":string,"summary":string}'
                "\nGiải thích các trường:\n"
                "- property_type: 'apartment' (căn hộ), 'house' (nhà), 'land' (đất), 'commercial' (shophouse/mặt bằng), 'other' (khác)\n"
                "- intent: 'purchase' (mua), 'inquiry' (hỏi thông tin), 'complaint' (khiếu nại), 'other' (khác)\n"
                "- urgency: 'critical' (khẩn cấp, cần xem hôm nay), 'high' (cao, cần xem sớm), 'medium' (trung bình), 'low' (thấp)\n"
                "- sentiment: 'positive' (tích cực), 'neutral' (trung lập), 'negative' (tiêu cực)\n"
                "- summary: tóm tắt ngắn gọn nhu cầu khách hàng bằng tiếng Việt"
            ),
        },
        {"role": "user", "content": convo},
    ]
        analysis_json = analyze_agent.chat_text(messages=analysis_prompt, json_mode=True)
        analysis = normalize_extraction(json.loads(analysis_json))
        logger.info("Agent 5 analysis: %s", analysis)

        job = {
            "message_id": message_id,
            "channel": "telegram",
            "payload": {
                "raw_text": message_text,
                "customer_name": user.full_name,
                "phone": analysis.get("phone"),
                "property_type": analysis.get("property_type"),
                "location": analysis.get("location"),
                "intent": analysis.get("intent"),
                "urgency": analysis.get("urgency"),
                "sentiment": analysis.get("sentiment"),
                "language": analysis.get("language"),
                "summary": analysis.get("summary"),
                "telegram_chat_id": str(chat_id),
                "chat_history": history,
                # Persist Telegram auto-reply in CRM so UI can show it.
                "auto_reply_content": reply,
                "_pre_analyzed": True,
                "_telegram_replied": True,
            },
        }

        r = redis.from_url(REDIS_URL, decode_responses=True)
        await r.lpush(QUEUE_KEY, json.dumps(job))
        await r.aclose()

    except Exception as e:
        logger.error("Agent 5 analysis/CRM enqueue failed: %s", e)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot started (Agent 4 reply + Agent 5 CRM analyze)")
    application.run_polling()


if __name__ == "__main__":
    main()
