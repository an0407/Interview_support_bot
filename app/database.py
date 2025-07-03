from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv
 
load_dotenv()
 
DATABASE_URL = os.environ.get('DATABASE_URL')

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass



async def get_async_session() -> AsyncSession: # type: ignore
    async with async_session() as session:
        yield session