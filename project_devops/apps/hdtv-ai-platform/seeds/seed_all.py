"""Master seed runner — EVN HDTV AI Platform.

Chạy: python -m seeds.seed_all
Idempotent: có thể chạy lại không bị duplicate.

Thứ tự:
1.  users (không phụ thuộc)
2.  risk_rules (không phụ thuộc)
3.  dossiers (không phụ thuộc, trả về id_map)
4.  workflow_diagrams (phụ thuộc dossiers)
5.  alerts (phụ thuộc dossiers)
6.  appraisals (phụ thuộc dossiers)
7.  notifications (phụ thuộc users + dossiers)
8.  reference_documents (phụ thuộc dossiers + users)
9.  agent_plans + ai_audit_logs (phụ thuộc dossiers)
10. token_usage (30 ngày dữ liệu demo)
"""
import asyncio
import logging

from app.core.database import async_session_factory
from seeds.seed_users import seed_users
from seeds.seed_risk_rules import seed_risk_rules
from seeds.seed_dossiers import seed_dossiers
from seeds.seed_workflow_diagrams import seed_workflow_diagrams
from seeds.seed_alerts import seed_alerts
from seeds.seed_appraisals import seed_appraisals
from seeds.seed_notifications import seed_notifications
from seeds.seed_reference_documents import seed_reference_documents
from seeds.seed_agent_plans import seed_agent_plans
from seeds.seed_token_usage import seed_token_usage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("=" * 50)
    logger.info("  HDTV AI — EVN Seed Data Runner")
    logger.info("=" * 50)

    async with async_session_factory() as session:
        # Step 1: Users
        logger.info("\n[1/10] Seeding users...")
        user_id_map = await seed_users(session)
        logger.info("  → %d users ready", len(user_id_map))

        # Step 2: Risk Rules
        logger.info("\n[2/10] Seeding risk rules...")
        await seed_risk_rules(session)

        # Step 3: Dossiers
        logger.info("\n[3/10] Seeding dossiers...")
        dossier_id_map = await seed_dossiers(session)
        logger.info("  → %d dossiers ready", len(dossier_id_map))

        # Step 4: Workflow Diagrams
        logger.info("\n[4/10] Seeding workflow diagrams (BPMN)...")
        await seed_workflow_diagrams(session, dossier_id_map)

        # Step 5: Alerts
        logger.info("\n[5/10] Seeding alerts...")
        await seed_alerts(session, dossier_id_map)

        # Step 6: Appraisals
        logger.info("\n[6/10] Seeding appraisal results...")
        await seed_appraisals(session, dossier_id_map)

        # Step 7: Notifications
        logger.info("\n[7/10] Seeding notifications...")
        await seed_notifications(session, user_id_map, dossier_id_map)

        # Step 8: Reference documents (tài liệu kèm hồ sơ UAV thật)
        logger.info("\n[8/10] Seeding reference documents (UAV dossier)...")
        admin_id = user_id_map.get("admin@evnhanoi.vn", 1)
        await seed_reference_documents(session, dossier_id_map, uploader_id=admin_id)

        # Step 9: Agent plans + AI audit logs
        logger.info("\n[9/10] Seeding agent plans & audit logs (UAV appraisal trace)...")
        await seed_agent_plans(session, dossier_id_map)

    # Step 10: Token usage (own session — has internal commit)
    logger.info("\n[10/10] Seeding token usage (30 days demo data)...")
    await seed_token_usage()

    logger.info("\n" + "=" * 50)
    logger.info("  Seed hoàn tất!")
    logger.info("  Users: %d | Dossiers: %d", len(user_id_map), len(dossier_id_map))
    logger.info("  Demo login: admin@evnhanoi.vn / EVN@2024!")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
