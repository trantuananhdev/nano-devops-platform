# API Contract — EVN HDTV

Base URL: `/api/v1`

## Health

```
GET /health
200 {"status":"ok","service":"hdtv-ai-platform"}
```

## Dossiers

```
GET /dossiers
200 [{id, doc_no, title, unit, risk_level, status, created_at}]

GET /dossiers/{id}
200 {id, doc_no, title, unit, risk_level, status, pdf_url, appraisal: {...}|null}

POST /dossiers/{id}/appraise
202 {task_id, dossier_id, status:"queued"}

GET /dossiers/{id}/pdf-url
200 {dossier_id, pdf_url, expires_in:3600}
404 if no PDF uploaded
```

## Search

```
GET /search?q=&risk=&status=
200 {hits:[...], query, processingTimeMs, estimatedTotalHits}
     (_degraded:true if Meilisearch unreachable)
```

## Workflows

```
GET /workflows/{dossier_id}
200 {dossier_id, bpmn_xml, updated_at}
404 if not saved

PUT /workflows/{dossier_id}
200 {dossier_id, bpmn_xml, updated_at}
Body: {bpmn_xml: "<xml...>"}
```

## Admin

```
GET /users
200 [{id, name, email, dept, role, status}]

GET /roles
200 [{id, name, desc, users_count}]

GET /system-logs
200 [{id, time, user, action, details, type}]
```

## Alerts

```
GET /alerts?status=open
200 [{id, dossier_id, severity, source, description, status}]

PATCH /alerts/{id}/resolve
200 {id, status:"resolved"}
```

## Audit Logs

```
GET /audit-logs?limit=50
200 [{id, task_id, tool_name, execution_time_ms, inputs, outputs, created_at}]
```

## Meta (Dashboard, Tools, Graph)

```
GET /tools
200 [{name, description, category, status, usage_count, last_used_at}]

GET /knowledge-graph?dossier_id=1
200 {dossier_id, dossier_title, nodes[], edges[]}

GET /dashboard/summary
200 {pending_count, high_risk_count, approved_count, open_alerts, alert_sources[], notable_dossiers[]}

GET /schedules
200 [{id, name, cron, schedule_text, tools[], status, description}]

GET /skills
200 [{id, name, description, type, is_active, markdown_content}]

GET /checklist-template
200 [{id, text, type, is_required}]
```

## WebSocket

```
WS /ws/appraisal/{dossier_id}

Events (JSON):
{type:"started"|"tool_executing"|"tool_result"|"risk_flagged"|"completed", ...}
```

## Error Format

```json
{"detail": "message"}
```
