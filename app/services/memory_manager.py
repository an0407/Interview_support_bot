from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.db.memory_model import ChatHistory

class MemoryManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_message(self, session_id: str, user_input: str, assistant_response: str):
        chat = ChatHistory(
            session_id=session_id,
            user_input=user_input,
            assistant_response=assistant_response
        )
        self.session.add(chat)
        await self.session.commit()

    async def get_history(self, session_id: str) -> List[tuple[str, str]]:
        result = await self.session.execute(
            select(ChatHistory).where(ChatHistory.session_id == session_id).order_by(ChatHistory.created_at)
        )
        chats = result.scalars().all()
        return [(chat.user_input, chat.assistant_response) for chat in chats]
