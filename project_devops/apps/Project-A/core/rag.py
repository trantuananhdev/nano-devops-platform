from typing import List, Dict
import asyncio

class RAGManager:
    """
    Quản lý việc truy xuất lịch sử các phiên thảo luận của Teen.
    Trong thực tế, đây sẽ là nơi kết nối với pgvector hoặc Pinecone.
    """
    def __init__(self, vector_db_url: str = None):
        self.vector_db_url = vector_db_url

    async def retrieve_history(self, teen_id: str, k: int = 3) -> str:
        """
        Truy xuất tóm tắt của k phiên thảo luận gần nhất để làm ngữ cảnh.
        Mô phỏng việc truy xuất từ Vector DB.
        """
        # Giả lập độ trễ truy xuất
        await asyncio.sleep(0.5)

        # Mock data: Lịch sử giả lập để AI có cái để so sánh
        mock_history = {
            "teen_123": [
                "Tuần 1: Teen cảm thấy áp lực học tập trung bình, lo lắng về kỳ thi toán sắp tới.",
                "Tuần 2: Teen có mâu thuẫn nhỏ với bạn thân, tâm trạng hơi trầm xuống.",
                "Tuần 3: Teen đã làm hòa với bạn, tâm trạng ổn định hơn nhưng vẫn lo lắng về điểm số."
            ]
        }

        history_list = mock_history.get(teen_id, ["Không có lịch sử trước đó."])
        
        # Kết hợp thành một chuỗi ngữ cảnh
        context = "\n".join(history_list[:k])
        return f"Lịch sử các tuần trước:\n{context}"
