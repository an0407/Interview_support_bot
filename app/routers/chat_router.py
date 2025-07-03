from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session

from app.models.pydantic.chat_payload import AdminPayload
from app.services.chat_service import ChatService
 
router = APIRouter(prefix="/chat", tags = ['AI_chat'])
 
@router.post('/', response_model=dict)
async def ai_chat(question: AdminPayload, db: AsyncSession = Depends(get_async_session)):
    return await ChatService(db).chat(chat_data=question)
