from datetime import datetime
from sqlalchemy import Column, Integer, Date, Text, DateTime, JSON
from app.core.database import Base


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    tasks_completed_count = Column(Integer, default=0)
    procrastination_notes = Column(Text, nullable=True)
    user_mood = Column(String(50), nullable=True)
    partner_energy_level = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    raw_insights = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
