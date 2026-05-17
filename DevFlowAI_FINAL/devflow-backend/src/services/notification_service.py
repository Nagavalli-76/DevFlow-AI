class NotificationService:
    @staticmethod
    async def create(db, user_id: str, notif_type: str, title: str, body: str, data: dict = None):
        return await db.notification.create(data={
            "userId": user_id,
            "type": notif_type,
            "title": title,
            "body": body,
            "data": data,
        })
