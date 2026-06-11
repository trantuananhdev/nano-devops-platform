# Self-Critique Checklist (run after each task)

## Architecture
- [ ] LLM called only via HTTP (`LLM_BASE_URL`), never embedded in FastAPI
- [ ] Celery handles long-running ReAct loops (API returns 202)
- [ ] Every tool call logged to `ai_audit_logs`

## Code Quality
- [ ] Async/await for DB, HTTP, tools
- [ ] Router → Service → Repository separation
- [ ] No hardcoded IPs/keys (Pydantic Settings + .env)
- [ ] Type hints on all public functions

## Frontend
- [ ] No changes to CSS variables or `.glass-panel`
- [ ] Pinia stores for API state
- [ ] WebSocket wrapper with exponential backoff reconnect

## Ops
- [ ] `test.sh` passes
- [ ] `docker-compose.hdtv.yml` has memory limits
- [ ] Health endpoint responds

## Security
- [ ] LLM port 8080 UFW restricted to VM IP
- [ ] Secrets in .env only, not committed
