from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, String, Date, DateTime, ForeignKey, JSON
from app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    # category: food, transport, household, shopping, bills, medical, travel, other
    category = Column(String(50), default="food", index=True)
    note = Column(String(255), nullable=True)
    receipt_image_url = Column(String(500), nullable=True)
    raw_ocr_data = Column(JSON, nullable=True)
    expense_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
