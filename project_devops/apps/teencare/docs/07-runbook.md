# Production Runbook

## On-call priorities

1) **Safety** (hallucination/grounding fail/high-risk)  
2) **Delivery SLA** (\<5 phút)  
3) **Cost** (USD/session)  
4) **Quality** (actionability, feedback)

## Monitoring dashboard (real-time)

- Latency p50/p95/p99 per step
- Hallucination flag rate (rolling 24h)
- Grounding score distribution
- Cost per session
- Parent app open rate sau notification

## Incident playbooks

### Hallucination burst

Trigger: hallucination rate > 10% trong 1 ngày

Actions:

- Bật **circuit breaker**: dừng auto-delivery, chuyển mentor review
- Snapshot logs: prompt_version, model_id, input stats (turns, quality_score)
- Root-cause: transcript ngắn/noise/dialect/topic mới
- Hotfix: tăng threshold, siết prompt constraints, judge coverage
- Shadow mode trước khi mở lại delivery

### Delivery delay / timeout

Trigger: delivery > 5 phút hoặc pipeline timeouts

Actions:

- Enable fallback: trả cached last summary + `flag="stale_data"`
- Reduce context (cắt Layer 2)
- Degrade gracefully: deliver partial insights nếu validation pass

### Cost spike

Trigger: cost/session tăng > 50% so với baseline

Actions:

- Audit context assembly (token bloat)
- Giảm history chunks
- Giảm judge coverage (chỉ high-risk)
- Xem xét model nhỏ hơn cho Step 1/Step 2

## Rollback policy

- Rollback ngay nếu:
  - schema validity < 100%
  - hallucination rate tăng đột biến
  - parent complaints tăng nhanh

## Release checklist

- Prompt_version bumped
- A/B test configured
- Alerts updated
- Golden set eval run
- Runbook updated nếu có thay đổi behavior

