# Alert Rules — CRM Pipeline

Worker (`crm-ai-worker`) đánh giá sau khi LLM trả JSON và **trước** khi commit transaction (hoặc ngay sau INSERT).

---

## 1. Environment variables

| Variable | Required | Mô tả |
|----------|----------|-------|
| `TELEGRAM_BOT_TOKEN` | One of TG/Lark | Bot token |
| `TELEGRAM_CHAT_ID` | With TG | Leader group chat id |
| `LARK_WEBHOOK_URL` | One of TG/Lark | Incoming webhook URL |
| `ALERT_ENABLED` | No | default `true` |
| `ALERT_COOLDOWN_SECONDS` | No | default `60` — chống spam cùng `message_id` |

Secret files (compose Task 3.6):
- `crm_telegram_bot_token`
- `crm_telegram_chat_id`

---

## 2. Rule matrix

| Rule ID | Điều kiện (OR trong nhóm) | alert_type | Ưu tiên |
|---------|---------------------------|------------|---------|
| **R1_HOT** | `urgency` IN (`high`, `critical`) | `hot_lead` | P1 |
| **R2_NEGATIVE** | `sentiment` = `negative` | `negative_sentiment` | P1 |
| **R3_CANCEL** | `intent` = `cancel_order` | `cancel_intent` | P0 (cao nhất) |
| **R4_COMPLAINT** | `intent` = `complaint` AND `sentiment` = `negative` | `complaint_escalation` | P1 |

**Gửi alert nếu:** bất kỳ rule match AND `ALERT_ENABLED=true`.

**Không gửi nếu:** `alert_sent=true` trên record (idempotent) hoặc cooldown key `crm:alert:cooldown:{message_id}` còn TTL.

---

## 3. Message template (Telegram)

```
🚨 CRM Alert — {alert_type}
Channel: {channel}
Urgency: {urgency} | Sentiment: {sentiment}
Intent: {intent}
Customer: {customer_name} | Phone: {phone}
Product: {product_interest}
Summary: {summary}
Message ID: {message_id}
Time: {processed_at}
```

**R3_CANCEL** thêm prefix: `⚠️ CANCEL RISK — `

---

## 4. Lark payload

```json
{
  "msg_type": "text",
  "content": {
    "text": "<same formatted text as Telegram>"
  }
}
```

POST `LARK_WEBHOOK_URL` — timeout 5s, không retry quá 2 lần.

---

## 5. Implementation pseudocode (Task 3.5)

```python
def evaluate_alerts(lead: LeadRow) -> Optional[str]:
    if lead.intent == "cancel_order":
        return "cancel_intent"
    if lead.urgency in ("high", "critical"):
        return "hot_lead"
    if lead.sentiment == "negative":
        return "negative_sentiment"
    if lead.intent == "complaint" and lead.sentiment == "negative":
        return "complaint_escalation"
    return None

async def send_alert(alert_type: str, lead: LeadRow):
    if not ALERT_ENABLED:
        return
    if await cooldown_active(lead.message_id):
        return
    text = format_message(alert_type, lead)
    if TELEGRAM_BOT_TOKEN:
        await telegram_send(text)
    if LARK_WEBHOOK_URL:
        await lark_send(text)
    CRM_ALERTS_SENT.labels(alert_type=alert_type).inc()
    await set_cooldown(lead.message_id)
```

---

## 6. Demo scenarios (phỏng vấn)

| # | raw_text (gợi ý) | Rule kích hoạt |
|---|------------------|----------------|
| 1 | "Cancel my order!!! scam" | R3_CANCEL + R2_NEGATIVE |
| 2 | "09171234567 need 50 units today" | R1_HOT |
| 3 | "serum price?" | Không alert (inquiry neutral) |

---

## 7. Observability

- Metric: `crm_alerts_sent_total{alert_type}`
- Log: `INFO alert_sent message_id=... type=cancel_intent`
- Grafana panel: alerts/hour by type (Task 3.8)

---

## 8. Failure behavior

| Lỗi | Hành vi |
|-----|---------|
| Telegram 429/5xx | Log error; `alert_sent=false`; có thể retry manual |
| Lark timeout | Same |
| DB update fail | Không đánh dấu sent — at-least-once alert risk chấp nhận demo |

Production hardening (ghi chú): dead-letter alert channel — out of Phase 3 scope.
