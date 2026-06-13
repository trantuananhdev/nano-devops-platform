"""Master seed runner — EVN HDTV AI Platform.

Chạy: python -m seeds.seed_all
Idempotent: có thể chạy lại không bị duplicate.

Thứ tự:
1. users (không phụ thuộc)
2. risk_rules (không phụ thuộc)
3. dossiers (không phụ thuộc, trả về id_map)
4. workflow_diagrams (phụ thuộc dossiers)
5. alerts (phụ thuộc dossiers)
6. appraisals (phụ thuộc dossiers)
7. notifications (phụ thuộc users + dossiers)
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
        logger.info("\n[1/7] Seeding users...")
        user_id_map = await seed_users(session)
        logger.info("  → %d users ready", len(user_id_map))

        # Step 2: Risk Rules
        logger.info("\n[2/7] Seeding risk rules...")
        await seed_risk_rules(session)

        # Step 3: Dossiers
        logger.info("\n[3/7] Seeding dossiers...")
        dossier_id_map = await seed_dossiers(session)
        logger.info("  → %d dossiers ready", len(dossier_id_map))

        # Step 4: Workflow Diagrams
        logger.info("\n[4/7] Seeding workflow diagrams (BPMN)...")
        await seed_workflow_diagrams(session, dossier_id_map)

        # Step 5: Alerts
        logger.info("\n[5/7] Seeding alerts...")
        await seed_alerts(session, dossier_id_map)

        # Step 6: Appraisals
        logger.info("\n[6/7] Seeding appraisal results...")
        await seed_appraisals(session, dossier_id_map)

        # Step 7: Notifications
        logger.info("\n[7/7] Seeding notifications...")
        await seed_notifications(session, user_id_map, dossier_id_map)

    logger.info("\n" + "=" * 50)
    logger.info("  Seed hoàn tất!")
    logger.info("  Users: %d | Dossiers: %d", len(user_id_map), len(dossier_id_map))
    logger.info("  Demo login: admin@evnhanoi.vn / EVN@2024!")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
