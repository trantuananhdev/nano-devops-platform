import os
import json
from openai import AsyncOpenAI
from schemas import BehavioralInsight
from dotenv import load_dotenv

load_dotenv()

class AIEngine:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_insight(self, transcript: str, history_context: str = "") -> BehavioralInsight:
        """
        Phân tích transcript và history để tạo báo cáo behavioral report.
        """
        system_prompt = """Bạn là một Senior AI Engineer tại TeenCare. 
Nhiệm vụ của bạn là chuyển đổi transcript hội thoại giữa Mentor và Teen thành báo cáo hành vi có cấu trúc cho phụ huynh.
Báo cáo của bạn phải dựa trên thực tế từ transcript và xem xét sự thay đổi so với lịch sử các tuần trước.
Tránh hoàn toàn việc tự suy diễn (hallucination). Nếu không có đủ dữ liệu, hãy ghi chú rõ.

Phản hồi phải luôn ở định dạng JSON chuẩn theo schema sau:
{
  "emotion_summary": "Tóm tắt ngắn gọn tâm trạng",
  "risk_level": "low" | "medium" | "high",
  "key_topics": ["topic 1", "topic 2"],
  "behavioral_patterns": "So sánh với lịch sử",
  "parent_action_items": ["hành động 1", "hành động 2"],
  "confidence_score": 0.0 - 1.0
}
"""

        user_prompt = f"""## DỮ LIỆU ĐẦU VÀO
{history_context}

## TRANSCRIPT HIỆN TẠI
{transcript}

Hãy thực hiện phân tích ngay bây giờ:
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            # Parse JSON và chuyển đổi thành BehavioralInsight object
            raw_result = json.loads(response.choices[0].message.content)
            return BehavioralInsight(**raw_result)

        except Exception as e:
            # Fallback nếu có lỗi (ví dụ: API key không hợp lệ trong môi trường test)
            return BehavioralInsight(
                emotion_summary=f"Lỗi khi gọi AI: {str(e)}",
                risk_level="low",
                key_topics=["Error"],
                behavioral_patterns="Không thể phân tích.",
                parent_action_items=["Kiểm tra lại hệ thống."],
                confidence_score=0.0
            )
