from sqlalchemy import (
    Column, Integer, String,
    DateTime, Text, Date
)
from app.database import Base
from datetime import datetime, timezone

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(Text)
    joining_date = Column(Date)
    experience = Column(Integer)
    email = Column(String, unique=True)
    interview_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)