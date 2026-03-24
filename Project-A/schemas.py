from pydantic import BaseModel, Field
from typing import List, Optional

class BehavioralInsight(BaseModel):
    emotion_summary: str = Field(..., description="Tóm tắt trạng thái cảm xúc hiện tại")
    risk_level: str = Field(..., description="Mức độ rủi ro: low, medium, high")
    key_topics: List[str] = Field(..., description="Danh sách các chủ đề chính đã thảo luận")
    parent_action_items: List[str] = Field(..., description="Các hành động cụ thể cha mẹ có thể thực hiện")
    confidence_score: float = Field(..., ge=0, le=1, description="Độ tin cậy của AI")
