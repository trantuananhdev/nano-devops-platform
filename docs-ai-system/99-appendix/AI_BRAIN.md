# Project Brain

## Source of Truth

The following files contain COMPLETE project knowledge:

- [`final_ai_context.md`](final_ai_context.md) — architecture, agent, schema, API
- [`final_devops_context.md`](final_devops_context.md) — topology, env, deploy

Never reinvent architecture. Always consult these contexts.

---

## Cognitive Rules

AI must NEVER read entire repository blindly.

AI selects knowledge intentionally.

| Task type | Read |
|-----------|------|
| Architecture / Agent | `final_ai_context.md` |
| Infrastructure / Deploy | `final_devops_context.md` |
| Current work | `HDTV_TASK.md`, `PROJECT_STATE.md` |
| API wiring | `API_CONTRACT.md` |
| After task | `SELF_CRITIQUE.md` |

Implementation → Architecture boundaries in `final_ai_context.md`  
Debugging → `final_devops_context.md` + `./cli.sh hdtv-logs`
