import logging
from datetime import datetime, date
from typing import Dict, Any
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.task import Task
from app.models.shift import Shift
from app.models.expense import Expense
from app.services.telegram_service import telegram_service
from app.services.ai_gateway import ai_gateway

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/telegram")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Webhook endpoint รับข้อมูลอัปเดตจาก Telegram Bot"""
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to read webhook payload: {e}")
        return {"ok": False}

    # 1. Handle Inline Button Clicks (Callback Queries)
    if "callback_query" in data:
        await handle_callback_query(data["callback_query"], db)
        return {"ok": True}

    # 2. Handle Normal Messages
    if "message" in data:
        await handle_incoming_message(data["message"], db)

    return {"ok": True}


async def handle_callback_query(cb: Dict[str, Any], db: AsyncSession):
    cb_id = cb.get("id")
    cb_data = cb.get("data", "")
    from_user = cb.get("from", {})
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    user_name = from_user.get("first_name", "คุณแฟน")

    logger.info(f"Callback received: {cb_data} from {user_name}")

    # Acknowledge shift selections
    if cb_data.startswith("shift_"):
        shift_type_map = {
            "shift_morning": ("เวรเช้า (08:00 - 16:00)", "06:30", "07:15"),
            "shift_afternoon": ("เวรบ่าย (16:00 - 24:00)", "13:30", "15:15"),
            "shift_night": ("เวรดึก (24:00 - 08:00)", "21:30", "23:15"),
            "shift_off": ("วันหยุด (Off) 🎉", None, None),
        }
        shift_info = shift_type_map.get(cb_data, ("ไม่ระบุ", None, None))
        name_label, wake_time, drop_time = shift_info

        if wake_time and drop_time:
            reply = (
                f"✅ <b>บันทึกเวรเรียบร้อยครับ!</b>\n"
                f"พรุ่งนี้คุณแฟน: <b>{name_label}</b>\n"
                f"⏰ แนะนำตื่นนอน: <b>{wake_time} น.</b>\n"
                f"🚗 คุณพี่เตรียมขับรถไปส่งเวลา: <b>{drop_time} น.</b> ครับ"
            )
        else:
            reply = f"🎉 <b>เย้! พรุ่งนี้คุณแฟนได้หยุด (Off-เวร)</b> พักผ่อนให้เต็มที่เลยครับ!"

        await telegram_service.send_message(chat_id, reply)

    # Acknowledge In-charge care buttons
    elif cb_data in ["partner_drank_water", "partner_snacked", "partner_busy"]:
        reactions = {
            "partner_drank_water": "💧 เยี่ยมมากครับ! ร่างกายไม่ขาดน้ำ ลุยต่อได้!",
            "partner_snacked": "🥪 เก่งมากครับ ได้พลังงานรองท้องแล้ว มีแรงสู้คนไข้ต่อ!",
            "partner_busy": "🏃 รับทราบครับ! สู้ๆ นะครับ เดี๋ยวก็ลงเวรแล้ว เป็นกำลังใจให้ครับ 🩵"
        }
        await telegram_service.send_message(chat_id, reactions[cb_data])


async def handle_incoming_message(msg: Dict[str, Any], db: AsyncSession):
    chat_id = msg.get("chat", {}).get("id")
    from_user = msg.get("from", {})
    user_telegram_id = from_user.get("id")
    user_name = from_user.get("first_name", "User")

    # กำหนด role ผู้ส่ง (คุณ หรือ แฟน)
    is_partner = str(user_telegram_id) == str(settings.PARTNER_TELEGRAM_ID)
    sender_role = "nurse" if is_partner else "freelancer"

    # 1. ข้อความเสียง (Voice Note) -> ใช้ Groq Whisper แปลงเป็นตัวหนังสือ
    if "voice" in msg:
        voice_file_id = msg["voice"]["file_id"]
        await telegram_service.send_message(chat_id, "🎙 <i>กำลังฟังข้อความเสียงด้วย Groq Whisper...</i>")
        audio_bytes = await telegram_service.get_file_bytes(voice_file_id)
        if audio_bytes:
            transcribed_text = await ai_gateway.transcribe_audio_groq(audio_bytes)
            if transcribed_text:
                await telegram_service.send_message(
                    chat_id, f"🗣 <b>ถอดความได้ว่า:</b> \"{transcribed_text}\""
                )
                # ส่งข้อความที่แปลงได้ไปประมวลผลต่อเหมือนพิมพ์ข้อความมา
                await process_text_intent(transcribed_text, sender_role, chat_id, db)
            else:
                await telegram_service.send_message(chat_id, "ฟังข้อความเสียงไม่ชัดเจน ลองพูดใหม่อีกครั้งนะครับ")
        return

    # 2. รูปถ่ายสลิป / ใบเสร็จ (Photo) -> ใช้ Gemini Vision อ่านข้อมูล
    if "photo" in msg:
        # ดึงรูปขนาดใหญ่สุด
        photo_file_id = msg["photo"][-1]["file_id"]
        caption = msg.get("caption", "")
        await telegram_service.send_message(chat_id, "🧾 <i>กำลังสแกนสลิปด้วย Gemini Vision...</i>")

        photo_bytes = await telegram_service.get_file_bytes(photo_file_id)
        if photo_bytes:
            slip_data = await ai_gateway.analyze_slip_gemini(photo_bytes)
            amount = slip_data.get("amount", 0)
            category = slip_data.get("category", "food")
            note = slip_data.get("note") or caption or "สลิปโอนเงิน"

            if amount > 0:
                # บันทึกลงฐานข้อมูล Expense
                expense = Expense(
                    amount=amount,
                    category=category,
                    note=note,
                    raw_ocr_data=slip_data,
                    expense_date=date.today()
                )
                db.add(expense)
                await db.commit()

                reply = (
                    f"✅ <b>บันทึกบัญชีครัวเรือนเรียบร้อยครับ!</b>\n"
                    f"💰 ยอดเงิน: <b>{amount:,.2f} บาท</b>\n"
                    f"🏷 หมวดหมู่: <b>{category}</b>\n"
                    f"📝 รายละเอียด: {note}"
                )
                await telegram_service.send_message(chat_id, reply)
            else:
                await telegram_service.send_message(
                    chat_id, "ไม่พบตัวเลขยอดเงินในรูปสลิปครับ รบกวนพิมพ์ยอดเงินบอกแทนได้เลยครับ"
                )
        return

    # 3. ข้อความปกติ (Text)
    if "text" in msg:
        text = msg["text"].strip()
        await process_text_intent(text, sender_role, chat_id, db)


async def process_text_intent(text: str, sender_role: str, chat_id: int | str, db: AsyncSession):
    """ส่งข้อความเข้า DeepSeek เพื่อแยกเจตนาและบันทึกลงฐานข้อมูล"""
    intent_result = await ai_gateway.parse_intent_deepseek(text, sender_role=sender_role)
    intent = intent_result.get("intent", "general_chat")
    data = intent_result.get("data", {})
    reply_suggestion = intent_result.get("reply_suggestion", "รับทราบครับ!")

    logger.info(f"Parsed intent: {intent}, Data: {data}")

    # Case A: เพิ่มงานลูกค้า (task_add / task_urgent)
    if intent in ["task_add", "task_urgent"]:
        title = data.get("title") or text
        client = data.get("client_name") or "ทั่วไป"
        priority = data.get("priority", "urgent" if intent == "task_urgent" else "normal")

        new_task = Task(
            title=title,
            client_name=client,
            priority=priority,
            status="todo"
        )
        db.add(new_task)
        await db.commit()

        priority_emoji = "🚨 งานด่วน!" if priority in ["urgent", "high"] else "📌 บันทึกงานใหม่"
        msg = (
            f"{priority_emoji}\n"
            f"<b>งาน:</b> {title}\n"
            f"<b>ลูกค้า:</b> {client}\n"
            f"<b>ความสำคัญ:</b> {priority}\n\n"
            f"{reply_suggestion}"
        )
        await telegram_service.send_message(chat_id, msg)

    # Case B: บันทึกรายจ่าย (expense จากการพิมพ์บอก)
    elif intent == "expense":
        amount = data.get("amount", 0)
        category = data.get("category", "food")
        title = data.get("title") or text

        if amount > 0:
            expense = Expense(
                amount=amount,
                category=category,
                note=title,
                expense_date=date.today()
            )
            db.add(expense)
            await db.commit()

            msg = (
                f"💰 <b>บันทึกรายจ่ายเรียบร้อย!</b>\n"
                f"ยอด: <b>{amount:,.2f} บาท</b> ({category})\n"
                f"รายการ: {title}\n\n"
                f"{reply_suggestion}"
            )
            await telegram_service.send_message(chat_id, msg)
        else:
            await telegram_service.send_message(chat_id, reply_suggestion)

    # Case C: อื่นๆ / พูดคุยทั่วไป
    else:
        await telegram_service.send_message(chat_id, reply_suggestion)
