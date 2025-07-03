from sqlalchemy import (
    Column, Integer, String,
    DateTime, Text, Date, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone

class Interview(Base):
    __tablename__ = 'interviews'

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="SET NULL"))
    interview_date = Column(Date)
    l1_count = Column(Integer)
    l2_count = Column(Integer)
    l3_count = Column(Integer)
    is_active = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default = None)

    admin = relationship("Admin", back_populates="interview")