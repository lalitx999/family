import asyncio
import logging
from app.workers.celery_app import celery_app
from app.services.telegram_service import telegram_service

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async coroutines in synchronous Celery tasks"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task
def send_morning_briefing():
    """07:30 น. Morning Protocol (สรุปงาน + เวรแฟน + ดักคอห้ามขึ้นเตียง)"""
    msg = (
        "🌅 <b>อรุณสวัสดิ์ครับทุกคน!</b>\n\n"
        "ส่งคุณแฟนเรียบร้อยแล้วใช่ไหมครับ? ⚠️ <b>คำเตือนฉุกเฉิน: ห้ามเอนตัวลงเตียงเด็ดขาดนะ!</b>\n"
        "เปิดคอม ดื่มน้ำ 1 แก้ว แล้วลุย 25 นาทีแรกกันก่อนครับ!\n\n"
        "📌 <i>วันนี้มีงานด่วนของลูกค้าคนไหนต้องเคลียร์ พิมพ์บอกหรือส่งเสียงมาได้เลยครับ</i>"
    )
    run_async(telegram_service.send_group_message(msg))
    logger.info("Sent morning briefing")


@celery_app.task
def send_lunch_break_reminder():
    """12:00 น. พักเที่ยง 1 ชม."""
    msg = (
        "🍱 <b>เที่ยงแล้วครับทุกคน! พักเบรคสายตา 1 ชม.</b>\n\n"
        "พักหน้าจอ ลุกขึ้นยืดเส้นยืดสาย ไปหาของอร่อยๆ ทานเติมพลังกันครับ\n"
        "แล้วเจอกันตอนบ่ายโมงตรงครับผม! ⏳"
    )
    run_async(telegram_service.send_group_message(msg))
    logger.info("Sent lunch reminder")


@celery_app.task
def send_afternoon_kickoff():
    """13:00 น. ปลุกเริ่มงานช่วงบ่าย"""
    msg = (
        "⚡️ <b>บ่ายโมงตรงแล้วครับ! หมดเวลาพักเบรค</b>\n\n"
        "กลับมาประจำการที่โต๊ะทำงาน ลุยงานช่วงบ่ายให้เสร็จไวๆ จะได้มีเวลาพักผ่อนตอนเย็นครับ! 🚀"
    )
    run_async(telegram_service.send_group_message(msg))
    logger.info("Sent afternoon kickoff")


@celery_app.task
def send_incharge_support_nudge():
    """15:00 น. เช็กดูแลแฟนอินชาร์จ (โหมดห่วงใย ไม่กดดัน)"""
    # ปุ่มลัดสำหรับแฟนกด 0.5 วินาที
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "💧 จิบน้ำแล้ว", "callback_data": "partner_drank_water"},
                {"text": "🥪 ทานขนมแล้ว", "callback_data": "partner_snacked"},
            ],
            [
                {"text": "🏃 กำลังยุ่งมากกก", "callback_data": "partner_busy"}
            ]
        ]
    }
    msg = (
        "🩺 <b>แวะมาส่งกำลังใจรอบบ่ายครับ!</b>\n\n"
        "คุณแฟนถ้าวันนี้งานหนัก/เป็นอินชาร์จ อย่าลืมหาจังหวะจิบน้ำหรือหยิบขนมรองท้องนิดนึงนะครับ 🩵\n"
        "<i>(ข้อความนี้ไม่ต้องพิมพ์ตอบนะครับ หรือแตะปุ่มลัดด้านล่างได้เลย สู้ๆ ครับ!)</i>"
    )
    run_async(telegram_service.send_group_message(msg, reply_markup=reply_markup))
    logger.info("Sent incharge support nudge")


@celery_app.task
def send_daily_finance_reminder():
    """20:00 น. เช็กบิลค่าใช้จ่ายประจำวัน"""
    msg = (
        "💰 <b>เช็กบิลบัญชีครัวเรือนประจำวันครับ!</b>\n\n"
        "วันนี้ทั้ง 2 คนใช้จ่ายเงินไปคนละกี่บาทบ้างครับ?\n"
        "• พิมพ์ยอดสั้นๆ ได้เลย (เช่น <i>'ซื้อของ 150'</i> หรือ <i>'ค่าข้าว 60'</i>)\n"
        "• หรือส่งรูปสลิปโอนเงิน / ใบเสร็จ เข้ามาได้เลย เดี๋ยว Gemini ช่วยอ่านยอดให้ครับ! 🧾"
    )
    run_async(telegram_service.send_group_message(msg))
    logger.info("Sent daily finance reminder")


@celery_app.task
def send_night_work_review():
    """23:00 น. ทวงสรุปงานคุณ (Freelancer)"""
    msg = (
        "🌙 <b>23:00 น. ได้เวลาทบทวนผลงานวันนี้ครับ!</b>\n\n"
        "วันนี้งานลูกค้าที่ตั้งเป้าไว้เรียบร้อยดีไหมครับ? ส่งงานครบไหม หรือมีงานไหนต้องยกไปพรุ่งนี้?\n"
        "พิมพ์สรุปสั้นๆ ให้ผมบันทึกเป็นสถิติหน่อยครับ พรุ่งนี้จะได้จัดคิวต่อให้ถูกทาง! ✨"
    )
    run_async(telegram_service.send_group_message(msg))
    logger.info("Sent night work review")


@celery_app.task
def send_night_shift_partner():
    """23:10 น. ถามเวรแฟนสำหรับวันพรุ่งนี้"""
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🌅 เวรเช้า (08:00)", "callback_data": "shift_morning"},
                {"text": "☀️ เวรบ่าย (16:00)", "callback_data": "shift_afternoon"},
            ],
            [
                {"text": "🌙 เวรดึก (24:00)", "callback_data": "shift_night"},
                {"text": "🏖 วันหยุด (Off)", "callback_data": "shift_off"},
            ]
        ]
    }
    msg = (
        "🩺 <b>คุณแฟนครับ พรุ่งนี้ขึ้นเวรไหนเอ่ย?</b>\n\n"
        "กดเลือกปุ่มด้านล่างได้เลยครับ จะได้คำนวณเวลาตื่นนอนและเวลาที่คุณแฟนต้องไปส่งถูกครับ 😴"
    )
    run_async(telegram_service.send_group_message(msg, reply_markup=reply_markup))
    logger.info("Sent night shift partner question")
