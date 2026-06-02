FROM python:3.12-slim

WORKDIR /app

COPY telegram-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared worker modules (5-agent Gemini + CRM helpers)
COPY crm-ai-worker/src/geminiProvider.py .
COPY crm-ai-worker/src/config.py .
COPY crm-ai-worker/src/agents.py .
COPY crm-ai-worker/src/llm_gemini.py .
COPY crm-ai-worker/src/metrics.py .
COPY crm-ai-worker/src/compliance_guard.py .

COPY telegram-bot/main.py .

CMD ["python", "main.py"]
