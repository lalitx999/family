from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Time, Boolean, Text, ForeignKey
from app.core.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shift_date = Column(Date, nullable=False, index=True)
    # shift_type: morning (เช้า 08:00-16:00), afternoon (บ่าย 16:00-24:00), night (ดึก 24:00-08:00), off (วันหยุด)
    shift_type = Column(String(50), nullable=False)
    is_incharge = Column(Boolean, default=False)
    wake_up_time = Column(Time, nullable=True)
    drop_off_time = Column(Time, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
