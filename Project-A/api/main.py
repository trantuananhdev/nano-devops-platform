from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse
from schemas import BehavioralInsight
import uvicorn

app = FastAPI(title="TeenCare AI Platform")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "teencare-ai"}

@app.post("/analyze/session")
async def analyze_session(transcript: str):
    # TODO: Implement AI analysis logic
    return {"message": "Analysis started"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
