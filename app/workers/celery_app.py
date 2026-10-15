from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "family_assistant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    timezone="Asia/Bangkok",
    enable_utc=False,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"]
)

# -------------------------------------------------------------
# Celery Beat Periodic Schedule (ตารางเวลาอัตโนมัติประจำวัน)
# -------------------------------------------------------------
celery_app.conf.beat_schedule = {
    # 1. 07:30 น. Morning Protocol (สรุปงาน + เวรแฟน + ปลุกเปิดคอม)
    "morning_routine_730": {
        "task": "app.workers.tasks.send_morning_briefing",
        "schedule": crontab(hour=7, minute=30),
    },
    # 2. 12:00 น. Lunch Break (เตือนพักเที่ยง 1 ชม.)
    "lunch_break_1200": {
        "task": "app.workers.tasks.send_lunch_break_reminder",
        "schedule": crontab(hour=12, minute=0),
    },
    # 3. 13:00 น. Afternoon Kickoff (เรียกกลับมาลุยงานบ่าย)
    "afternoon_kickoff_1300": {
        "task": "app.workers.tasks.send_afternoon_kickoff",
        "schedule": crontab(hour=13, minute=0),
    },
    # 4. 15:00 น. In-Charge Support (สะกิดให้เตรียมดูแลแฟนอินชาร์จ)
    "incharge_support_1500": {
        "task": "app.workers.tasks.send_incharge_support_nudge",
        "schedule": crontab(hour=15, minute=0),
    },
    # 5. 20:00 น. Household Finance (เช็กบิลค่าใช้จ่ายประจำวัน)
    "evening_finance_2000": {
        "task": "app.workers.tasks.send_daily_finance_reminder",
        "schedule": crontab(hour=20, minute=0),
    },
    # 6. 23:00 น. Night Work Review (ทวงสรุปงานคุณ)
    "night_work_review_2300": {
        "task": "app.workers.tasks.send_night_work_review",
        "schedule": crontab(hour=23, minute=0),
    },
    # 7. 23:10 น. Night Shift & Rest (ถามเวรแฟน + เตือนเวลานอน)
    "night_shift_partner_2310": {
        "task": "app.workers.tasks.send_night_shift_partner",
        "schedule": crontab(hour=23, minute=10),
    },
}
