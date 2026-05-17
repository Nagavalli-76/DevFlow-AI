from prisma import Prisma
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = Prisma()

    async def connect(self):
        try:
            await self.client.connect()
            logger.info("PostgreSQL connected via Prisma")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def disconnect(self):
        await self.client.disconnect()
        logger.info("PostgreSQL disconnected")

    def get_client(self) -> Prisma:
        return self.client

db = Database()

# Dependency for FastAPI routes
async def get_db() -> Prisma:
    return db.get_client()
