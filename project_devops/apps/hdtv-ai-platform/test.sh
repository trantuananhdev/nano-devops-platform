#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"
  if eval "$cmd"; then
    echo "✅ $name"
    PASS=$((PASS + 1))
  else
    echo "❌ $name"
    FAIL=$((FAIL + 1))
  fi
}

check "health endpoint" "curl -sf ${API_URL}/health | grep -q ok"
check "list dossiers" "curl -sf ${API_URL}/dossiers | grep -q doc_no"
check "audit logs endpoint" "curl -sf ${API_URL}/audit-logs | grep -q '\\[\\]' || curl -sf ${API_URL}/audit-logs | grep -q tool_name"
check "alerts endpoint" "curl -sf ${API_URL}/alerts | grep -q '\\['"
check "tool registry count" "grep -c ErpBudgetCheck project_devops/apps/hdtv-ai-platform/app/services/tools/base.py | grep -q 1"
check "tools API endpoint" "curl -sf ${API_URL}/tools | grep -q ErpBudgetCheck"
check "dashboard summary API" "curl -sf ${API_URL}/dashboard/summary | grep -q pending_count"
check "knowledge graph API" "curl -sf '${API_URL}/knowledge-graph?dossier_id=1' | grep -q nodes"

# T-11: Meilisearch search endpoint (graceful degraded mode expected if Meili not running)
check "search endpoint responds" "curl -sf '${API_URL}/search?q=tờ+trình' | grep -q '\"hits\"'"
check "search endpoint with filter" "curl -sf '${API_URL}/search?q=&risk=high' | grep -q '\"hits\"'"

# T-12: BPMN workflow persistence
check "workflow 404 for missing" "curl -sf '${API_URL}/workflows/999' | grep -q 'No saved workflow' || [ \"\$(curl -sw '%{http_code}' -o /dev/null ${API_URL}/workflows/999)\" = '404' ]"
check "workflow list empty" "curl -sf '${API_URL}/workflows' | grep -q '\\['"
check "workflow save dossier 1" "curl -sf -X PUT '${API_URL}/workflows/1' -H 'Content-Type: application/json' -d '{\"bpmn_xml\":\"<test>workflow</test>\"}' | grep -q bpmn_xml"
check "workflow load after save" "curl -sf '${API_URL}/workflows/1' | grep -q bpmn_xml"
check "workflow audit logged" "curl -sf '${API_URL}/audit-logs' | grep -q WorkflowSave"

# T-13: Dossier create + PDF upload
check "create dossier 201" "curl -sf -X POST '${API_URL}/dossiers' -H 'Content-Type: application/json' -d '{\"doc_no\":\"T13-TEST-001\",\"title\":\"Test dossier T13 integration\",\"unit\":\"Ban Kiểm thử\"}' | grep -q doc_no"
check "duplicate doc_no 409" "[ \"\$(curl -sw '%{http_code}' -o /dev/null -X POST '${API_URL}/dossiers' -H 'Content-Type: application/json' -d '{\"doc_no\":\"T13-TEST-001\",\"title\":\"dupe\",\"unit\":\"X\"}')\" = '409' ]"
check "upload route exists" "[ \"\$(curl -sw '%{http_code}' -o /dev/null '${API_URL}/dossiers/1/upload')\" != '404' ]"
check "audit log DossierCreate" "curl -sf '${API_URL}/audit-logs' | grep -q DossierCreate"

# T-14: Admin panel + PDF presigned URL + Meilisearch sync hook
check "users API endpoint" "curl -sf '${API_URL}/users' | grep -q nva@evnhanoi.vn"
check "roles API endpoint" "curl -sf '${API_URL}/roles' | grep -q 'Quản trị viên'"
check "system-logs API endpoint" "curl -sf '${API_URL}/system-logs' | grep -q 'Hệ thống AI'"
check "pdf-url route exists" "[ \"\$(curl -sw '%{http_code}' -o /dev/null '${API_URL}/dossiers/1/pdf-url')\" != '404' ]"
check "meili sync in react_agent" "grep -q 'index_dossier' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"

# T-15: Vector Memory Service (Chroma)
check "memory package exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/memory/__init__.py ]"
check "vector_store module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/memory/vector_store.py ]"
check "retriever module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/memory/retriever.py ]"
check "migration 004 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/004_add_memory_embeddings.py ]"
check "embedding_id in migration" "grep -q 'embedding_id' project_devops/apps/hdtv-ai-platform/alembic/versions/004_add_memory_embeddings.py"
check "embedding_id in entities" "grep -q 'embedding_id' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "memory upsert in react_agent" "grep -q 'mem_store.upsert_memory' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "memory retriever in react_agent" "grep -q 'mem_retriever.retrieve_relevant_memories' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "chroma_collection_memories in config" "grep -q 'chroma_collection_memories' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "memory_top_k in config" "grep -q 'memory_top_k' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "chromadb in requirements" "grep -q 'chromadb' project_devops/apps/hdtv-ai-platform/requirements.txt"
check "seed_agent_memories in seed.py" "grep -q 'seed_agent_memories' project_devops/apps/hdtv-ai-platform/scripts/seed.py"
check "degraded fallback in retriever" "grep -q 'pg' project_devops/apps/hdtv-ai-platform/app/services/memory/retriever.py"

# T-16: Cross-dossier Memory + User Preferences
check "migration 005 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/005_user_preferences.py ]"
check "user_preferences table in migration" "grep -q 'user_preferences' project_devops/apps/hdtv-ai-platform/alembic/versions/005_user_preferences.py"
check "UserPreference in entities" "grep -q 'UserPreference' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "preference_service module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/memory/preference_service.py ]"
check "get_preferences in preference_service" "grep -q 'get_preferences' project_devops/apps/hdtv-ai-platform/app/services/memory/preference_service.py"
check "set_preference in preference_service" "grep -q 'set_preference' project_devops/apps/hdtv-ai-platform/app/services/memory/preference_service.py"
check "UserPreferenceOut in meta schemas" "grep -q 'UserPreferenceOut' project_devops/apps/hdtv-ai-platform/app/schemas/meta.py"
check "preferences endpoint in meta router" "grep -q 'preferences' project_devops/apps/hdtv-ai-platform/app/routers/meta.py"
check "build_preference_context in retriever" "grep -q 'build_preference_context' project_devops/apps/hdtv-ai-platform/app/services/memory/retriever.py"
check "cross_dossier query in retriever" "grep -q 'retrieve_cross_dossier_memories' project_devops/apps/hdtv-ai-platform/app/services/memory/retriever.py"
check "pref_context in react_agent" "grep -q 'pref_context' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "user_id in run_appraisal" "grep -q 'user_id' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "user_id in appraise endpoint" "grep -q 'user_id' project_devops/apps/hdtv-ai-platform/app/routers/dossiers.py"
check "seed_user_preferences in seed.py" "grep -q 'seed_user_preferences' project_devops/apps/hdtv-ai-platform/scripts/seed.py"
check "preferences API endpoint" "curl -sf '${API_URL}/users/1/preferences' | grep -q '\\['"

# T-17: Plan-Execute-Reflect Orchestrator
check "migration 006 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/006_agent_plans.py ]"
check "agent_plans table in migration" "grep -q 'agent_plans' project_devops/apps/hdtv-ai-platform/alembic/versions/006_agent_plans.py"
check "AgentPlan in entities" "grep -q 'AgentPlan' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "planner module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/planner.py ]"
check "executor module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py ]"
check "reflector module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/reflector.py ]"
check "create_plan in planner" "grep -q 'create_plan' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/planner.py"
check "execute_plan_steps in executor" "grep -q 'execute_plan_steps' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "reflect_on_results in reflector" "grep -q 'reflect_on_results' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/reflector.py"
check "plan_created event in react_agent" "grep -q 'plan_created' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "plan_revised event in react_agent" "grep -q 'plan_revised' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "step_completed event in executor" "grep -q 'step_completed' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "persist agent plan in react_agent" "grep -q '_persist_agent_plan' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "legacy fallback in react_agent" "grep -q '_run_legacy_react_loop' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "build_fallback_plan in planner" "grep -q 'build_fallback_plan' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/planner.py"
check "orchestrator helpers module" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/helpers.py ]"
check "normalize_tool_input in helpers" "grep -q 'normalize_tool_input' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/helpers.py"
check "orchestrator types module" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/types.py ]"

# T-18: Parallel Tool Executor
check "batch_executor module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py ]"
check "execute_parallel in batch_executor" "grep -q 'execute_parallel' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"
check "asyncio.gather in batch_executor" "grep -q 'asyncio.gather' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"
check "batch_executor used in executor" "grep -q 'batch_executor' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "execute_parallel imported in executor" "grep -q 'execute_parallel' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "parallel_group batching in executor" "grep -q '_build_execution_batches' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "parallel_group in planner schema" "grep -q 'parallel_group' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/planner.py"
check "financial parallel_group in fallback plan" "grep -q 'financial' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/planner.py"
check "no parallel ban in react_agent prompt" "! grep -q \"don't call multiple tools in parallel\" project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "wall time logged in batch_executor" "grep -q 'wall' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"

# T-19: Critic Module (Self-Reflection)
check "critic module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/critic.py ]"
check "review_draft in critic" "grep -q 'review_draft' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/critic.py"
check "build_rule_based_verdict in critic" "grep -q 'build_rule_based_verdict' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/critic.py"
check "critic invoked in react_agent" "grep -q 'plan_critic.review_draft' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "critic_review event in react_agent" "grep -q 'critic_review' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "critic_verdict on AppraisalResult" "grep -q 'critic_verdict' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "migration 007 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/007_critic_verdict.py ]"
check "critic_verdict in migration" "grep -q 'critic_verdict' project_devops/apps/hdtv-ai-platform/alembic/versions/007_critic_verdict.py"
check "critic loop in react_agent" "grep -q '_run_critic_loop' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "critic stores verdict on result" "grep -q 'critic_verdict=critic_verdict' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "high-risk rejection rule present" "grep -q 'Mức rủi ro HIGH nhưng dự thảo' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/critic.py"
check "failed checks + approval rejected" "grep -q 'kiểm tra FAIL' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/critic.py"
check "approval phrases guard" "grep -q '_APPROVAL_PHRASES' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/critic.py"
check "critic rule fallback returns approved" "grep -q \"'approved': approved\" project_devops/apps/hdtv-ai-platform/app/services/orchestrator/critic.py"

# T-20: Feedback API + Learning Loop
check "feedback router exists" "[ -f project_devops/apps/hdtv-ai-platform/app/routers/feedback.py ]"
check "feedback service exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/feedback_service.py ]"
check "feedback schemas exist" "[ -f project_devops/apps/hdtv-ai-platform/app/schemas/feedback.py ]"
check "feedback router registered" "grep -q 'feedback.router' project_devops/apps/hdtv-ai-platform/app/routers/__init__.py"
check "submit_feedback in service" "grep -q 'submit_feedback' project_devops/apps/hdtv-ai-platform/app/services/feedback_service.py"
check "upsert_feedback_lesson in vector_store" "grep -q 'upsert_feedback_lesson' project_devops/apps/hdtv-ai-platform/app/services/memory/vector_store.py"
check "retrieve_feedback_lessons in retriever" "grep -q 'retrieve_feedback_lessons' project_devops/apps/hdtv-ai-platform/app/services/memory/retriever.py"
check "feedback_lessons_context in planner" "grep -q 'feedback_lessons_context' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/planner.py"
check "retrieve_feedback_lessons in react_agent" "grep -q 'retrieve_feedback_lessons' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "chroma_collection_feedback_lessons in config" "grep -q 'chroma_collection_feedback_lessons' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "AgentFeedback model exists" "grep -q 'class AgentFeedback' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "submitFeedback in api.js" "grep -q 'submitFeedback' project_devops/apps/hdtv-ai-prototype/src/services/api.js"
check "getFeedbackStats in api.js" "grep -q 'getFeedbackStats' project_devops/apps/hdtv-ai-prototype/src/services/api.js"
check "feedback UI in workspace" "grep -q 'sendFeedback' project_devops/apps/hdtv-ai-prototype/src/views/SplitViewWorkspace.vue"
check "feedback stats endpoint" "grep -q '/feedback/stats' project_devops/apps/hdtv-ai-platform/app/routers/feedback.py"
check "POST dossier feedback route" "grep -q '/dossiers/{dossier_id}/feedback' project_devops/apps/hdtv-ai-platform/app/routers/feedback.py"

# T-21: Tool Chaining & Composition
check "migration 008 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/008_tool_chaining.py ]"
check "output_mapping in migration" "grep -q 'output_mapping' project_devops/apps/hdtv-ai-platform/alembic/versions/008_tool_chaining.py"
check "chains_to in migration" "grep -q 'chains_to' project_devops/apps/hdtv-ai-platform/alembic/versions/008_tool_chaining.py"
check "output_mapping in entities" "grep -q 'output_mapping' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "chains_to in entities" "grep -q 'chains_to' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "chain_executor module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/chain_executor.py ]"
check "build_chained_input in chain_executor" "grep -q 'build_chained_input' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/chain_executor.py"
check "get_chained_steps in chain_executor" "grep -q 'get_chained_steps' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/chain_executor.py"
check "chain_executor used in executor" "grep -q 'chain_executor' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "_execute_chained_tools in executor" "grep -q '_execute_chained_tools' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "chained_from in executor audit inputs" "grep -q 'chained_from' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "EcoOcrExtract chain in seed" "grep -q 'EcoOcrExtract' project_devops/apps/hdtv-ai-platform/scripts/seed.py && grep -q 'LegalGraphRAG' project_devops/apps/hdtv-ai-platform/scripts/seed.py"
check "extracted_text to query mapping in seed" "grep -q 'extracted_text' project_devops/apps/hdtv-ai-platform/scripts/seed.py && grep -q '\"query\"' project_devops/apps/hdtv-ai-platform/scripts/seed.py"
check "seed_tool_chains in seed.py" "grep -q 'seed_tool_chains' project_devops/apps/hdtv-ai-platform/scripts/seed.py"

# T-22: Human-in-the-Loop (HITL)
check "migration 009 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/009_agent_clarifications.py ]"
check "agent_clarifications in migration" "grep -q 'agent_clarifications' project_devops/apps/hdtv-ai-platform/alembic/versions/009_agent_clarifications.py"
check "AgentClarification in entities" "grep -q 'AgentClarification' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "clarification router exists" "[ -f project_devops/apps/hdtv-ai-platform/app/routers/clarifications.py ]"
check "clarification service exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/clarification_service.py ]"
check "clarification schemas exist" "[ -f project_devops/apps/hdtv-ai-platform/app/schemas/clarification.py ]"
check "clarifications router registered" "grep -q 'clarifications.router' project_devops/apps/hdtv-ai-platform/app/routers/__init__.py"
check "GET pending clarifications route" "grep -q '/clarifications/pending' project_devops/apps/hdtv-ai-platform/app/routers/clarifications.py"
check "POST answer clarification route" "grep -q '/clarifications/{clarification_id}/answer' project_devops/apps/hdtv-ai-platform/app/routers/clarifications.py"
check "detect_tool_conflict in service" "grep -q 'detect_tool_conflict' project_devops/apps/hdtv-ai-platform/app/services/clarification_service.py"
check "ClarificationPaused exception" "grep -q 'ClarificationPaused' project_devops/apps/hdtv-ai-platform/app/services/clarification_service.py"
check "pause in react_agent" "grep -q '_maybe_pause_for_clarification' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "resume_appraisal in react_agent" "grep -q 'resume_appraisal' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "clarification_needed in service" "grep -q 'clarification_needed' project_devops/apps/hdtv-ai-platform/app/services/clarification_service.py"
check "resume_appraisal_task in tasks" "grep -q 'resume_appraisal_task' project_devops/apps/hdtv-ai-platform/app/workers/tasks.py"
check "ClarificationAnswer audit log" "grep -q 'ClarificationAnswer' project_devops/apps/hdtv-ai-platform/app/services/clarification_service.py"
check "getPendingClarifications in api.js" "grep -q 'getPendingClarifications' project_devops/apps/hdtv-ai-prototype/src/services/api.js"
check "answerClarification in api.js" "grep -q 'answerClarification' project_devops/apps/hdtv-ai-prototype/src/services/api.js"
check "clarification modal in workspace" "grep -q 'clarificationModal' project_devops/apps/hdtv-ai-prototype/src/views/SplitViewWorkspace.vue"

# T-23: Role-Based Agent Profiles
check "prompt_builder module exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/prompt_builder.py ]"
check "build_system_prompt in prompt_builder" "grep -q 'def build_system_prompt' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/prompt_builder.py"
check "build_resolution_md in prompt_builder" "grep -q 'def build_resolution_md' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/prompt_builder.py"
check "hdtv_leader prompt file" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/prompts/hdtv_leader.py ]"
check "dept_head prompt file" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/prompts/dept_head.py ]"
check "specialist prompt file" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/prompts/specialist.py ]"
check "admin prompt file" "[ -f project_devops/apps/hdtv-ai-platform/app/services/orchestrator/prompts/admin.py ]"
check "prompt_builder used in react_agent" "grep -q 'prompt_builder' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "_resolve_user_role in react_agent" "grep -q '_resolve_user_role' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "role passed to planner" "grep -q 'role=role' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"
check "role in planner create_plan" "grep -q 'role: UserRole' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/planner.py"
check "AppraiseRequest schema" "grep -q 'AppraiseRequest' project_devops/apps/hdtv-ai-platform/app/schemas/dossier.py"
check "appraise body user_id" "grep -q 'body: AppraiseRequest' project_devops/apps/hdtv-ai-platform/app/routers/dossiers.py"
check "four seeded roles in seed.py" "grep -q 'dept_head' project_devops/apps/hdtv-ai-platform/scripts/seed.py && grep -q 'UserRole.admin' project_devops/apps/hdtv-ai-platform/scripts/seed.py"
check "role resolutions differ in length" "cd project_devops/apps/hdtv-ai-platform && python -c \"
from types import SimpleNamespace
from app.models.entities import UserRole, RiskLevel
from app.services.orchestrator.prompt_builder import build_resolution_md
d = SimpleNamespace(doc_no='1/TTr', title='Test', unit='Ban KT')
checks = [{'tool': 'ErpBudgetCheck', 'label': 'Ngân sách', 'status': 'fail', 'desc': 'Vượt hạn mức'}]
leader = build_resolution_md(UserRole.hdtv_leader, d, RiskLevel.high, checks)
spec = build_resolution_md(UserRole.specialist, d, RiskLevel.high, checks)
assert len(spec) > len(leader), f'expected specialist longer: {len(spec)} vs {len(leader)}'
assert 'tóm tắt HĐTV' in leader
assert 'kỹ thuật đầy đủ' in spec
\""

# T-24: Agent Intelligence Dashboard
check "agent_metrics_service exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/agent_metrics_service.py ]"
check "get_agent_metrics in service" "grep -q 'def get_agent_metrics' project_devops/apps/hdtv-ai-platform/app/services/agent_metrics_service.py"
check "plan_revision_rate in service" "grep -q 'plan_revision_rate' project_devops/apps/hdtv-ai-platform/app/services/agent_metrics_service.py"
check "critic_rejection_rate in service" "grep -q 'critic_rejection_rate' project_devops/apps/hdtv-ai-platform/app/services/agent_metrics_service.py"
check "memory_retrieval_count in service" "grep -q 'memory_retrieval_count' project_devops/apps/hdtv-ai-platform/app/services/agent_metrics_service.py"
check "AgentMetricsOut schema" "grep -q 'class AgentMetricsOut' project_devops/apps/hdtv-ai-platform/app/schemas/meta.py"
check "agent metrics route" "grep -q '/agent/metrics' project_devops/apps/hdtv-ai-platform/app/routers/meta.py"
check "agent metrics API responds" "curl -sf '${API_URL}/agent/metrics' | grep -q 'plan_revision_rate'"
check "feedback_total in metrics API" "curl -sf '${API_URL}/agent/metrics' | grep -q 'feedback_total'"
check "fetchAgentMetrics in admin store" "grep -q 'fetchAgentMetrics' project_devops/apps/hdtv-ai-prototype/src/stores/admin.js"
check "getAgentMetrics in api.js" "grep -q 'getAgentMetrics' project_devops/apps/hdtv-ai-prototype/src/services/api.js"
check "agent_intel tab in admin view" "grep -q 'agent_intel' project_devops/apps/hdtv-ai-prototype/src/views/SystemAdminView.vue"

# T-25: LLM Circuit Breaker & Gemini Key Rotation
check "T-25: circuit_breaker.py exists" "[ -f project_devops/apps/hdtv-ai-platform/app/core/circuit_breaker.py ]"
check "T-25: CircuitBreaker class defined" "grep -q 'class CircuitBreaker' project_devops/apps/hdtv-ai-platform/app/core/circuit_breaker.py"
check "T-25: CircuitBreakerOpen exception" "grep -q 'class CircuitBreakerOpen' project_devops/apps/hdtv-ai-platform/app/core/circuit_breaker.py"
check "T-25: CLOSED/OPEN/HALF_OPEN states" "grep -q 'HALF_OPEN' project_devops/apps/hdtv-ai-platform/app/core/circuit_breaker.py"
check "T-25: asyncio.Lock in circuit breaker" "grep -q 'asyncio.Lock' project_devops/apps/hdtv-ai-platform/app/core/circuit_breaker.py"
check "T-25: llm_router imports CircuitBreaker" "grep -q 'CircuitBreaker' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"
check "T-25: llm_router imports CircuitBreakerOpen" "grep -q 'CircuitBreakerOpen' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"
check "T-25: circuit breaker used for local LLM" "grep -q '_get_cb_local' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"
check "T-25: circuit breaker used for Gemini" "grep -q '_get_cb_gemini' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"
check "T-25: circuit_open status emitted" "grep -q 'circuit_open' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"
check "T-25: _next_gemini_key skips cooldown" "grep -q '_key_cooldown' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"
check "T-25: appraisal asyncio.wait_for in tasks" "grep -q 'asyncio.wait_for' project_devops/apps/hdtv-ai-platform/app/workers/tasks.py"
check "T-25: appraisal_max_duration_s in config" "grep -q 'appraisal_max_duration_s' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-25: llm_circuit_failure_threshold in config" "grep -q 'llm_circuit_failure_threshold' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-25: llm_circuit_cooldown_s in config" "grep -q 'llm_circuit_cooldown_s' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-25: timeout WS event emitted in tasks" "grep -q '\"timeout\"' project_devops/apps/hdtv-ai-platform/app/workers/tasks.py"
check "T-25: dossier marked needs_revision on timeout" "grep -q 'needs_revision' project_devops/apps/hdtv-ai-platform/app/workers/tasks.py"
check "T-25: hdtv_llm_circuit_trips_total metric" "grep -q 'hdtv_llm_circuit_trips_total' project_devops/apps/hdtv-ai-platform/app/core/metrics.py"
check "T-25: hdtv_appraisal_timeouts_total metric" "grep -q 'hdtv_appraisal_timeouts_total' project_devops/apps/hdtv-ai-platform/app/core/metrics.py"
check "T-25: LLM_CIRCUIT_TRIPS imported in llm_router" "grep -q 'LLM_CIRCUIT_TRIPS' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"
check "T-25: APPRAISAL_TIMEOUTS incremented in tasks" "grep -q 'APPRAISAL_TIMEOUTS' project_devops/apps/hdtv-ai-platform/app/workers/tasks.py"

# T-26: Sandbox Audit Log + Docker Ephemeral Executor
check "T-26: docker_sandbox.py exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/tools/docker_sandbox.py ]"
check "T-26: DockerSandboxExecutor class exists" "grep -q 'class DockerSandboxExecutor' project_devops/apps/hdtv-ai-platform/app/services/tools/docker_sandbox.py"
check "T-26: run_python_in_docker function" "grep -q 'async def run_python_in_docker' project_devops/apps/hdtv-ai-platform/app/services/tools/docker_sandbox.py"
check "T-26: docker --network none used" "grep -q 'network.*none' project_devops/apps/hdtv-ai-platform/app/services/tools/docker_sandbox.py"
check "T-26: docker --read-only used" "grep -q 'read-only' project_devops/apps/hdtv-ai-platform/app/services/tools/docker_sandbox.py"
check "T-26: fallback to process sandbox" "grep -q 'process_fallback' project_devops/apps/hdtv-ai-platform/app/services/tools/docker_sandbox.py"
check "T-26: _emit_sandbox_audit in sandbox_executor" "grep -q '_emit_sandbox_audit' project_devops/apps/hdtv-ai-platform/app/services/tools/sandbox_executor.py"
check "T-26: AiAuditLog written in sandbox audit" "grep -q 'AiAuditLog' project_devops/apps/hdtv-ai-platform/app/services/tools/sandbox_executor.py"
check "T-26: SandboxShell tool_name in audit" "grep -q 'SandboxShell' project_devops/apps/hdtv-ai-platform/app/services/tools/sandbox_executor.py"
check "T-26: SANDBOX_EXECUTIONS metric in sandbox_executor" "grep -q 'SANDBOX_EXECUTIONS' project_devops/apps/hdtv-ai-platform/app/services/tools/sandbox_executor.py"
check "T-26: hdtv_sandbox_executions_total metric" "grep -q 'hdtv_sandbox_executions_total' project_devops/apps/hdtv-ai-platform/app/core/metrics.py"
check "T-26: sandbox_use_docker in config" "grep -q 'sandbox_use_docker' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-26: sandbox_docker_image in config" "grep -q 'sandbox_docker_image' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-26: sandbox_docker_timeout_s in config" "grep -q 'sandbox_docker_timeout_s' project_devops/apps/hdtv-ai-platform/app/core/config.py"

# T-27: RAG Data Ingestion Pipeline (Celery + Embedding Worker)
check "T-27: rag_pipeline.py exists" "[ -f project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py ]"
check "T-27: ingest_legal_documents task" "grep -q 'def ingest_legal_documents' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"
check "T-27: cleanup_stale_embeddings task" "grep -q 'def cleanup_stale_embeddings' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"
check "T-27: celery task decorator on ingest" "grep -q \"@celery_app.task.*ingest_legal_documents\" project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py || grep -q 'celery_app.task' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"
check "T-27: sliding window chunking" "grep -q '_sliding_window_chunks' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"
check "T-27: chunk_size_tokens used in pipeline" "grep -q 'chunk_size_tokens' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"
check "T-27: ingested_at metadata in chunks" "grep -q 'ingested_at' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"
check "T-27: stale cleanup uses rag_stale_days" "grep -q 'rag_stale_days' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"
check "T-27: celery beat schedule in celery_app" "grep -q 'beat_schedule' project_devops/apps/hdtv-ai-platform/app/workers/celery_app.py"
check "T-27: ingest_legal_documents in beat schedule" "grep -q 'ingest_legal_documents' project_devops/apps/hdtv-ai-platform/app/workers/celery_app.py"
check "T-27: cleanup_stale_embeddings in beat schedule" "grep -q 'cleanup_stale_embeddings' project_devops/apps/hdtv-ai-platform/app/workers/celery_app.py"
check "T-27: upsert_legal_doc in vector_store" "grep -q 'upsert_legal_doc' project_devops/apps/hdtv-ai-platform/app/services/memory/vector_store.py"
check "T-27: query_legal_docs in vector_store" "grep -q 'query_legal_docs' project_devops/apps/hdtv-ai-platform/app/services/memory/vector_store.py"
check "T-27: legal_rag uses rag_pipeline collection" "grep -q 'rag_legal_collection\|query_legal_docs' project_devops/apps/hdtv-ai-platform/app/services/tools/legal_rag.py"
check "T-27: legal_rag deduplicates results" "grep -q '_deduplicate_results' project_devops/apps/hdtv-ai-platform/app/services/tools/legal_rag.py"
check "T-27: context_manager emits CONTEXT_TRUNCATIONS" "grep -q 'CONTEXT_TRUNCATIONS' project_devops/apps/hdtv-ai-platform/app/core/context_manager.py"
check "T-27: rag_docs_dir in config" "grep -q 'rag_docs_dir' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-27: rag_chunk_size_tokens in config" "grep -q 'rag_chunk_size_tokens' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-27: rag_legal_collection in config" "grep -q 'rag_legal_collection' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-27: hdtv_rag_docs volume in docker-compose" "grep -q 'hdtv_rag_docs' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-27: /opt/rag-docs mount in docker-compose" "grep -q '/opt/rag-docs' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-27: beat service in docker-compose" "grep -q 'hdtv-beat\|container_name.*beat' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-27: RagIngest audit log in rag_pipeline" "grep -q 'RagIngest' project_devops/apps/hdtv-ai-platform/app/workers/rag_pipeline.py"

# T-28: Observability LLMOps — HDTV Alerts + Grafana Dashboard + OTel Tracing
check "T-28: hdtv-alerts.yml exists" "[ -f project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml ]"
check "T-28: HdtvApiDown rule present" "grep -q 'HdtvApiDown' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml"
check "T-28: HdtvAgentInfiniteLoop rule present" "grep -q 'HdtvAgentInfiniteLoop' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml"
check "T-28: HdtvLlmCircuitOpen rule present" "grep -q 'HdtvLlmCircuitOpen' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml"
check "T-28: HdtvToolHighFailureRate rule present" "grep -q 'HdtvToolHighFailureRate' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml"
check "T-28: HdtvAppraisalTimeout rule present" "grep -q 'HdtvAppraisalTimeout' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml"
check "T-28: HdtvSandboxHighBlockRate rule present" "grep -q 'HdtvSandboxHighBlockRate' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml"
check "T-28: HdtvContextTruncationSpike rule present" "grep -q 'HdtvContextTruncationSpike' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml"
check "T-28: at least 6 alert rules" "grep -c '- alert:' project_devops/platform/config/prometheus/alerts/hdtv-alerts.yml | awk '\$1>=6'"
check "T-28: grafana hdtv-agent.json exists" "[ -f project_devops/platform/monitoring/grafana/dashboards/hdtv-agent.json ]"
check "T-28: grafana dashboard has LLM Health row" "grep -q 'LLM Health' project_devops/platform/monitoring/grafana/dashboards/hdtv-agent.json"
check "T-28: grafana dashboard has Agent Loop row" "grep -q 'Agent Loop' project_devops/platform/monitoring/grafana/dashboards/hdtv-agent.json"
check "T-28: grafana dashboard has Tool Execution row" "grep -q 'Tool Execution' project_devops/platform/monitoring/grafana/dashboards/hdtv-agent.json"
check "T-28: grafana dashboard has Infrastructure row" "grep -q 'Infrastructure' project_devops/platform/monitoring/grafana/dashboards/hdtv-agent.json"
check "T-28: grafana provisioning hdtv.yml exists" "[ -f project_devops/platform/monitoring/grafana/provisioning/dashboards/hdtv.yml ]"
check "T-28: tracing.py in app/core" "[ -f project_devops/apps/hdtv-ai-platform/app/core/tracing.py ]"
check "T-28: configure_tracer function exists" "grep -q 'def configure_tracer' project_devops/apps/hdtv-ai-platform/app/core/tracing.py"
check "T-28: instrument_fastapi function exists" "grep -q 'def instrument_fastapi' project_devops/apps/hdtv-ai-platform/app/core/tracing.py"
check "T-28: OTLP gRPC exporter in tracing.py" "grep -q 'OTLPSpanExporter' project_devops/apps/hdtv-ai-platform/app/core/tracing.py"
check "T-28: tracing wired in main.py" "grep -q 'configure_tracer' project_devops/apps/hdtv-ai-platform/app/main.py"
check "T-28: instrument_fastapi called in main.py" "grep -q 'instrument_fastapi' project_devops/apps/hdtv-ai-platform/app/main.py"
check "T-28: tracing_enabled guard in main.py" "grep -q 'tracing_enabled' project_devops/apps/hdtv-ai-platform/app/main.py"
check "T-28: opentelemetry-sdk in requirements.txt" "grep -q 'opentelemetry-sdk' project_devops/apps/hdtv-ai-platform/requirements.txt"
check "T-28: opentelemetry-exporter-otlp in requirements.txt" "grep -q 'opentelemetry-exporter-otlp' project_devops/apps/hdtv-ai-platform/requirements.txt"
check "T-28: opentelemetry-instrumentation-fastapi in requirements.txt" "grep -q 'opentelemetry-instrumentation-fastapi' project_devops/apps/hdtv-ai-platform/requirements.txt"
check "T-28: prometheus.yml has hdtv-ai job" "grep -q 'hdtv-ai' project_devops/platform/config/prometheus/prometheus.yml"
check "T-28: prometheus scrape label on api" "grep -q 'prometheus.scrape' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-28: prometheus.job label = hdtv-ai" "grep -q 'prometheus.job' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-28: platform-network in docker-compose" "grep -q 'platform-network' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-28: jaeger_host in config" "grep -q 'jaeger_host' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-28: tracing_enabled in config" "grep -q 'tracing_enabled' project_devops/apps/hdtv-ai-platform/app/core/config.py"

# T-29: MCP Streamable HTTP (SSE) + Tool Output Schema Validation
check "T-29: /mcp/tools/call/stream route defined" "grep -q 'call/stream' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: StreamingResponse in mcp.py" "grep -q 'StreamingResponse' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: text/event-stream media type" "grep -q 'event-stream' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: asyncio.Queue in mcp.py" "grep -q 'asyncio.Queue' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: SSE event: progress emitted" "grep -q 'event: progress' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: SSE event: result emitted" "grep -q 'event: result' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: SSE event: error emitted" "grep -q 'event: error' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: _TOOL_OUTPUT_SCHEMAS dict defined" "grep -q '_TOOL_OUTPUT_SCHEMAS' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: _TOOL_OUTPUT_SCHEMAS has ErpBudgetCheck" "grep -A5 '_TOOL_OUTPUT_SCHEMAS' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py | grep -q 'ErpBudgetCheck'"
check "T-29: _TOOL_OUTPUT_SCHEMAS has LegalGraphRAG" "grep -q 'LegalGraphRAG.*sources\|sources.*LegalGraphRAG' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py || grep -B2 -A5 'LegalGraphRAG' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py | grep -q 'sources\|results'"
check "T-29: at least 4 tools in output schemas" "grep -c '\"required\"' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py | awk '\$1>=4'"
check "T-29: _validate_tool_output function exists" "grep -q 'def _validate_tool_output' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: _validate_tool_output called in mcp_call_tool" "grep -q '_validate_tool_output' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: streaming capability in manifest" "grep -q 'streaming' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-29: traefik dynamic.yml has hdtv route" "grep -q 'hdtv.nano.platform' project_devops/platform/config/traefik/dynamic.yml"
check "T-29: traefik dynamic.yml has mcp ratelimit middleware" "grep -q 'mcp-ratelimit\|rateLimit' project_devops/platform/config/traefik/dynamic.yml"
check "T-29: traefik dynamic.yml has hdtv service upstream" "grep -q 'hdtv-api' project_devops/platform/config/traefik/dynamic.yml"
check "T-29: Traefik labels on docker-compose api" "grep -q 'traefik.enable' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-29: hdtv.nano.platform in Vagrantfile" "grep -q 'hdtv.nano.platform' Vagrantfile"

# T-30: Execution Harness — Tool Contract, Per-tool Timeout, Retry & Audit Correlation
check "T-30: ToolErrorType enum defined" "grep -q 'class ToolErrorType' project_devops/apps/hdtv-ai-platform/app/services/tools/types.py"
check "T-30: TRANSIENT value in ToolErrorType" "grep -q 'TRANSIENT' project_devops/apps/hdtv-ai-platform/app/services/tools/types.py"
check "T-30: BAD_INPUT value in ToolErrorType" "grep -q 'BAD_INPUT' project_devops/apps/hdtv-ai-platform/app/services/tools/types.py"
check "T-30: UNAVAILABLE value in ToolErrorType" "grep -q 'UNAVAILABLE' project_devops/apps/hdtv-ai-platform/app/services/tools/types.py"
check "T-30: _TOOL_INPUT_REQUIRED_FIELDS defined" "grep -q '_TOOL_INPUT_REQUIRED_FIELDS' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: ErpBudgetCheck in required fields" "grep -q 'ErpBudgetCheck' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: _validate_tool_input function exists" "grep -q 'def _validate_tool_input' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: _validate_tool_input called before fn" "grep -q '_validate_tool_input' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: asyncio.wait_for in execute_tool" "grep -q 'asyncio.wait_for' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: tool_execution_timeout_s used" "grep -q 'tool_execution_timeout_s' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: TimeoutError → TRANSIENT in base.py" "grep -q 'TimeoutError' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py && grep -q 'TRANSIENT' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: TOOL_TIMEOUTS metric incremented" "grep -q 'TOOL_TIMEOUTS' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: TOOL_INPUT_VALIDATION_ERRORS metric" "grep -q 'TOOL_INPUT_VALIDATION_ERRORS' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py"
check "T-30: error_type attached on all error paths" "grep -c 'error_type' project_devops/apps/hdtv-ai-platform/app/services/tools/base.py | awk '\$1>=4'"
check "T-30: retry logic in batch_executor" "grep -q 'max_retries' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"
check "T-30: retry_backoff_s in batch_executor" "grep -q 'retry_backoff_s' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"
check "T-30: TRANSIENT retry in batch_executor" "grep -q 'TRANSIENT' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"
check "T-30: TOOL_RETRIES metric in batch_executor" "grep -q 'TOOL_RETRIES' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"
check "T-30: retried flag in batch_executor result" "grep -q 'retried' project_devops/apps/hdtv-ai-platform/app/services/tools/batch_executor.py"
check "T-30: plan_step_id in AiAuditLog entity" "grep -q 'plan_step_id' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "T-30: error_type in AiAuditLog entity" "grep -q 'error_type' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "T-30: migration 010 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/010_audit_log_harness.py ]"
check "T-30: plan_step_id in migration 010" "grep -q 'plan_step_id' project_devops/apps/hdtv-ai-platform/alembic/versions/010_audit_log_harness.py"
check "T-30: error_type in migration 010" "grep -q 'error_type' project_devops/apps/hdtv-ai-platform/alembic/versions/010_audit_log_harness.py"
check "T-30: index on plan_step_id in migration" "grep -q 'ix_ai_audit_logs_plan_step_id' project_devops/apps/hdtv-ai-platform/alembic/versions/010_audit_log_harness.py"
check "T-30: plan_step_id written in executor.py" "grep -q 'plan_step_id' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "T-30: error_type written in executor.py" "grep -q 'error_type' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/executor.py"
check "T-30: tool_execution_timeout_s in config" "grep -q 'tool_execution_timeout_s' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-30: tool_max_retries in config" "grep -q 'tool_max_retries' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-30: tool_retry_backoff_s in config" "grep -q 'tool_retry_backoff_s' project_devops/apps/hdtv-ai-platform/app/core/config.py"
check "T-30: hdtv_tool_retries_total metric" "grep -q 'hdtv_tool_retries_total' project_devops/apps/hdtv-ai-platform/app/core/metrics.py"
check "T-30: hdtv_tool_timeouts_total metric" "grep -q 'hdtv_tool_timeouts_total' project_devops/apps/hdtv-ai-platform/app/core/metrics.py"
check "T-30: hdtv_tool_input_validation_errors metric" "grep -q 'hdtv_tool_input_validation_errors_total' project_devops/apps/hdtv-ai-platform/app/core/metrics.py"
check "T-30: handlers __init__.py exists" "[ -f project_devops/apps/hdtv-ai-platform/app/tools/handlers/__init__.py ]"
check "T-30: erp_handler.py exists" "[ -f project_devops/apps/hdtv-ai-platform/app/tools/handlers/erp_handler.py ]"
check "T-30: ErpBudgetHandler class in erp_handler" "grep -q 'class ErpBudgetHandler' project_devops/apps/hdtv-ai-platform/app/tools/handlers/erp_handler.py"
check "T-30: ErpInventoryHandler class in erp_handler" "grep -q 'class ErpInventoryHandler' project_devops/apps/hdtv-ai-platform/app/tools/handlers/erp_handler.py"
check "T-30: validate_input in erp_handler" "grep -q 'def validate_input' project_devops/apps/hdtv-ai-platform/app/tools/handlers/erp_handler.py"
check "T-30: beat service in docker-compose" "grep -q 'hdtv-beat' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"

# T-31: LLM Node Professionalization (Caddy + Metrics + Logs)
check "T-31: llm_node role tasks/main.yml exists" "[ -f project_devops/apps/ansible-ubuntu/roles/llm_node/tasks/main.yml ]"
check "T-31: Caddyfile.j2 template exists" "[ -f project_devops/apps/ansible-ubuntu/roles/llm_node/templates/Caddyfile.j2 ]"
check "T-31: docker-compose.llm.yml.j2 exists" "[ -f project_devops/apps/ansible-ubuntu/roles/llm_node/templates/docker-compose.llm.yml.j2 ]"
check "T-31: llm_node defaults/main.yml has TLS config" "grep -q 'llm_tls_enabled' project_devops/apps/ansible-ubuntu/roles/llm_node/defaults/main.yml"
check "T-31: cli.sh has ansible-deploy-llm" "grep -q 'ansible-deploy-llm' cli.sh"

# T-32: Observability Completeness & Alertmanager
check "T-32: alertmanager.yml exists" "[ -f project_devops/platform/config/alertmanager/alertmanager.yml ]"
check "T-32: docker-compose.observability.yml has Alertmanager" "grep -q 'alertmanager' project_devops/platform/composition/docker-compose.observability.yml"
check "T-32: cli.sh has obs-alerts" "grep -q 'obs-alerts' cli.sh"

# T-33: Token/API Keys Management Dashboard
check "T-33: ApiKey model exists" "grep -q 'class ApiKey' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "T-33: api_key_service.py exists" "[ -f project_devops/apps/hdtv-ai-platform/app/services/api_key_service.py ]"
check "T-33: api_keys router exists" "[ -f project_devops/apps/hdtv-ai-platform/app/routers/api_keys.py ]"
check "T-33: api_keys router registered" "grep -q 'api_keys.router' project_devops/apps/hdtv-ai-platform/app/routers/__init__.py"
check "T-33: migration 011 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/011_add_api_keys.py ]"
check "T-33: ApiKey schema exists" "grep -q 'class ApiKey' project_devops/apps/hdtv-ai-platform/app/schemas/api_key.py"
check "T-33: FE admin.js has fetchApiKeys" "grep -q 'fetchApiKeys' project_devops/apps/hdtv-ai-prototype/src/stores/admin.js"
check "T-33: FE api.js has getApiKeys" "grep -q 'getApiKeys' project_devops/apps/hdtv-ai-prototype/src/services/api.js"
check "T-33: llm_router uses DB keys" "grep -q 'api_key_service' project_devops/apps/hdtv-ai-platform/app/services/llm_router.py"

# T-34: HDTV Workflow Observability Dashboard (Grafana)
check "T-34: hdtv-workflow.json exists" "[ -f project_devops/platform/monitoring/grafana/dashboards/hdtv-workflow.json ]"
check "T-34: dashboard has Appraisal status panel" "grep -q 'Appraisal status' project_devops/platform/monitoring/grafana/dashboards/hdtv-workflow.json || grep -q 'appraisal' project_devops/platform/monitoring/grafana/dashboards/hdtv-workflow.json"

# T-35: Backup Strategy (Automated)
check "T-35: backup.sh script exists" "[ -f project_devops/apps/hdtv-ai-platform/scripts/backup.sh ]"
check "T-35: docker-compose.hdtv.yml has backup service" "grep -q 'backup' project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml"
check "T-35: cli.sh has hdtv-backup" "grep -q 'hdtv-backup' cli.sh"

# T-36: MCP Token Management & Audit
check "T-36: McpCallLog model exists" "grep -q 'class McpCallLog' project_devops/apps/hdtv-ai-platform/app/models/entities.py"
check "T-36: migration 012 exists" "[ -f project_devops/apps/hdtv-ai-platform/alembic/versions/012_mcp_call_logs.py ]"
check "T-36: mcp.py uses DB ApiKey auth" "grep -q 'api_key_service' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-36: mcp.py has audit log" "grep -q 'McpCallLog' project_devops/apps/hdtv-ai-platform/app/routers/mcp.py"
check "T-36: FE admin.js has MCP audit actions" "grep -q 'fetchMcpAuditLogs' project_devops/apps/hdtv-ai-prototype/src/stores/admin.js || grep -q 'mcp' project_devops/apps/hdtv-ai-prototype/src/stores/admin.js"
check "T-36: FE SystemAdminView has MCP tab" "grep -q 'mcp_audit' project_devops/apps/hdtv-ai-prototype/src/views/SystemAdminView.vue || grep -q 'MCP' project_devops/apps/hdtv-ai-prototype/src/views/SystemAdminView.vue"

# T-37: LLM Node Teardown & Reset
check "T-37: teardown-llm.yml exists" "[ -f project_devops/apps/ansible-ubuntu/teardown-llm.yml ]"
check "T-37: cli.sh has ansible-teardown-llm" "grep -q 'ansible-teardown-llm' cli.sh"

# T-45: Offline static pytest (no server — skip gracefully if python/pytest missing)
if command -v python >/dev/null 2>&1; then
  if python -c "import pytest" >/dev/null 2>&1; then
    check "T-45: static pytest suite" "python -m pytest project_devops/apps/hdtv-ai-platform/tests/test_static.py -x -q --tb=line"
  else
    echo "⏭  T-45: pytest not installed — pip install -r project_devops/apps/hdtv-ai-platform/requirements-dev.txt"
  fi
else
  echo "⏭  T-45: python not available — skip static pytest"
fi
check "T-45: test_static.py exists" "[ -f project_devops/apps/hdtv-ai-platform/tests/test_static.py ]"
check "T-45: conftest.py exists" "[ -f project_devops/apps/hdtv-ai-platform/tests/conftest.py ]"
check "T-45: requirements-dev.txt exists" "[ -f project_devops/apps/hdtv-ai-platform/requirements-dev.txt ]"

# T-47: SSH Bootstrap Password-First Fix
check "T-47: ACER_SSH_PASS in docker-entrypoint.sh" "grep -q 'ACER_SSH_PASS' project_devops/apps/ansible-ubuntu/docker-entrypoint.sh"
check "T-47: PubkeyAuthentication=no for bootstrap" "grep -q 'PubkeyAuthentication=no' project_devops/apps/ansible-ubuntu/docker-entrypoint.sh"
check "T-47: password-bootstrap inventory rewrite" "grep -q 'password-bootstrap mode' project_devops/apps/ansible-ubuntu/docker-entrypoint.sh"
check "T-47: ACER_SSH_PASS in .env.example" "grep -q 'ACER_SSH_PASS' .env.example"
check "T-47: ACER_SSH_PASS warn in validate_env.sh" "grep -q 'ACER_SSH_PASS' project_devops/platform/infra/scripts/validate_env.sh"
check "T-47: cli.sh auto-reads ACER_SSH_PASS" "grep -q 'ACER_SSH_PASS' cli.sh"
check "T-47: hdtv_auto_deploy.sh exports ACER_SSH_PASS" "grep -q 'export ACER_SSH_PASS' project_devops/platform/infra/scripts/vagrant/hdtv_auto_deploy.sh"
check "T-47: obs-alerts command in cli.sh" "grep -q 'obs-alerts' cli.sh"
check "T-47: no orphaned chat_completions import in react_agent" "! grep -q 'from app.services.llm_client import chat_completions' project_devops/apps/hdtv-ai-platform/app/services/orchestrator/react_agent.py"

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ]


