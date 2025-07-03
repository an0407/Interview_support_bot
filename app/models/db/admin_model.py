from sqlalchemy import (
    Column, Integer, String,
    DateTime, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(Text)
    email = Column(String, unique = True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default = None)

    interview = relationship("Interview", back_populates="admin")