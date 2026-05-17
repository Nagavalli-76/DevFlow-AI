"""
Seed script — run with: python seed.py
Creates demo users, teams, projects, tasks for hackathon demo
"""
import asyncio
from prisma import Prisma
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    db = Prisma()
    await db.connect()
    print("🌱 Seeding DevFlow AI database...")

    # ─── Demo User ───
    user = await db.user.upsert(
        where={"email": "nagavalli@devflow.ai"},
        data={
            "create": {
                "email": "nagavalli@devflow.ai",
                "username": "nagavalli76",
                "name": "Nagavalli",
                "passwordHash": pwd_context.hash("devflow123"),
                "role": "OWNER",
                "isVerified": True,
            },
            "update": {}
        }
    )
    print(f"  ✅ User: {user.email}")

    # ─── Demo Team ───
    team = await db.team.upsert(
        where={"slug": "devflow-team"},
        data={
            "create": {"name": "DevFlow Team", "slug": "devflow-team", "plan": "PRO"},
            "update": {}
        }
    )
    await db.teammember.upsert(
        where={"userId_teamId": {"userId": user.id, "teamId": team.id}},
        data={"create": {"userId": user.id, "teamId": team.id, "role": "OWNER"}, "update": {}}
    )
    print(f"  ✅ Team: {team.name}")

    # ─── Demo Projects ───
    for proj_data in [
        {"name": "DevFlow Frontend", "description": "React dashboard UI", "status": "ACTIVE"},
        {"name": "DevFlow Backend", "description": "FastAPI + PostgreSQL", "status": "ACTIVE"},
        {"name": "IBM BOB Integration", "description": "watsonx.ai chat service", "status": "IN_PROGRESS"},
    ]:
        p = await db.project.create(data={**proj_data, "ownerId": user.id, "teamId": team.id})
        print(f"  ✅ Project: {p.name}")

        # Tasks per project
        for task_data in [
            {"title": "Setup CI/CD pipeline", "status": "DONE", "priority": "HIGH"},
            {"title": "Write unit tests", "status": "IN_PROGRESS", "priority": "MEDIUM"},
            {"title": "Deploy to production", "status": "TODO", "priority": "CRITICAL"},
        ]:
            await db.task.create(data={**task_data, "projectId": p.id, "assigneeId": user.id})

    # ─── Welcome Notification ───
    await db.notification.create(data={
        "userId": user.id,
        "type": "SYSTEM",
        "title": "Welcome to DevFlow AI 🚀",
        "body": "Your IBM BOB-powered development partner is ready. Start coding!",
    })

    print("\n✅ Seed complete!")
    print("   Login: nagavalli@devflow.ai / devflow123")
    await db.disconnect()

asyncio.run(seed())
