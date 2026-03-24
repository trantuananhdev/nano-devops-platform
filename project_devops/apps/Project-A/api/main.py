from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from schemas import BehavioralInsight, SessionAnalysisRequest
from core.engine import AIEngine
from core.rag import RAGManager
import uvicorn
import json
import asyncio

app = FastAPI(title="TeenCare AI Platform")
engine = AIEngine()
rag = RAGManager()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "teencare-ai"}

@app.post("/analyze/session", response_model=BehavioralInsight)
async def analyze_session(request: SessionAnalysisRequest):
    """
    Phân tích một phiên thảo luận, có tích hợp RAG để lấy lịch sử.
    """
    try:
        # 1. Retrieval (RAG)
        history_context = await rag.retrieve_history(request.teen_id)

        # 2. Analysis (LLM Generation)
        insight = await engine.generate_insight(request.transcript, history_context)

        return insight
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/session/stream")
async def analyze_session_stream(request: SessionAnalysisRequest):
    """
    Mô phỏng Streaming response (SSE) cho trải nghiệm người dùng tốt hơn.
    Trong thực tế, AI engine sẽ stream trực tiếp từ LLM provider.
    """
    async def event_generator():
        # Step 1: Inform starting RAG
        yield "event: progress\ndata: Đang truy xuất lịch sử phiên thảo luận...\n\n"
        history_context = await rag.retrieve_history(request.teen_id)
        await asyncio.sleep(0.5)

        # Step 2: Inform starting AI Analysis
        yield "event: progress\ndata: Đang phân tích transcript và so sánh hành vi...\n\n"
        insight = await engine.generate_insight(request.transcript, history_context)
        await asyncio.sleep(0.5)

        # Step 3: Final JSON Insight
        yield f"event: result\ndata: {insight.json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
