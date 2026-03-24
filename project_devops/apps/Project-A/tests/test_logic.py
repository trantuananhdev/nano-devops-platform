import pytest
from httpx import AsyncClient
from api.main import app
from unittest.mock import patch, MagicMock
from schemas import BehavioralInsight

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "teencare-ai"}

@pytest.mark.asyncio
async def test_analyze_session_logic():
    # Mock AIEngine.generate_insight to avoid real LLM call
    mock_insight = BehavioralInsight(
        emotion_summary="Lo lắng về học tập",
        risk_level="medium",
        key_topics=["thi cử", "kỳ vọng"],
        behavioral_patterns="Duy trì sự lo lắng từ các tuần trước về điểm số.",
        parent_action_items=["Động viên con", "Không gây áp lực điểm số"],
        confidence_score=0.95
    )

    with patch("api.main.engine.generate_insight", return_value=mock_insight):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            payload = {
                "teen_id": "teen_123",
                "family_id": "family_abc",
                "transcript": "Test transcript content"
            }
            response = await ac.post("/analyze/session", json=payload)
            
    assert response.status_code == 200
    data = response.json()
    assert data["emotion_summary"] == "Lo lắng về học tập"
    assert data["risk_level"] == "medium"
    assert "confidence_score" in data
