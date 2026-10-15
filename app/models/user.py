from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    nickname = Column(String(50), nullable=True)
    role = Column(String(50), default="freelancer")  # "freelancer" หรือ "nurse"
    created_at = Column(DateTime, default=datetime.utcnow)
