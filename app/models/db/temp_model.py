from sqlalchemy import (
    Column, Integer, String,
    DateTime, Text, DATE
)
from app.database import Base
from datetime import datetime, timezone

class Temp(Base):
    __tablename__ = 'temporary'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(Text)
    level_chosen = Column(String, nullable = False)
    interview_date = Column(DATE)
    email = Column(String, nullable = False)
    admin_email = Column(String, nullable = False)
    interview_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)