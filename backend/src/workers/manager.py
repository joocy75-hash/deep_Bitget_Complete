import asyncio
import logging
from sqlalchemy import select

from ..database.models import BotStatus
from ..services.bot_runner import BotRunner

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(self, market_queue: asyncio.Queue, session_factory):
        self.market_queue = market_queue
        self.runner = BotRunner(market_queue)
        self.session_factory = session_factory

    async def bootstrap(self):
        """
        서버 시작 시 DB에서 is_running=True인 봇들을 복구합니다.
        개별 봇 시작 실패 시에도 다른 봇들의 복구는 계속 진행됩니다.
        """
        started_count = 0
        failed_count = 0

        async with self.session_factory() as session:
            result = await session.execute(
                select(BotStatus).where(BotStatus.is_running.is_(True))
            )
            bot_statuses = list(result.scalars())

            if not bot_statuses:
                logger.info("No bots to restore from database")
                return

            logger.info(f"Found {len(bot_statuses)} bot(s) to restore from database")

            for status in bot_statuses:
                try:
                    await self.runner.start(self.session_factory, status.user_id)
                    started_count += 1
                    logger.info(f"✅ Bot restored for user {status.user_id}")
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"❌ Failed to restore bot for user {status.user_id}: {e}"
                    )

            logger.info(
                f"Bot bootstrap complete: {started_count} started, {failed_count} failed "
                f"(out of {len(bot_statuses)} total)"
            )

    async def start_bot(self, user_id: int):
        await self.runner.start(self.session_factory, user_id)

    async def stop_bot(self, user_id: int):
        self.runner.stop(user_id)
