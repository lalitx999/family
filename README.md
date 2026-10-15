# 🏠 Family AI Butler (Life & Work OS)

ระบบเลขาและผู้จัดการชีวิตส่วนตัวสำหรับครอบครัว (ฟรีแลนซ์ WFH + พยาบาลอินชาร์จ) รันบน Home Server
ขับเคลื่อนด้วย **FastAPI + Celery + PostgreSQL + Redis + Telegram Bot** ร่วมกับ **AI Trio: Groq + DeepSeek + Gemini**

---

## 🚀 ฟังก์ชันหลัก (Core Features)

1. **🎙 Groq Whisper Voice-to-Action**: ส่งข้อความเสียงผ่าน Telegram แปลงเป็นข้อความใน 0.3 วินาที แล้วสั่งบันทึกงานหรือรายจ่ายได้ทันที
2. **🧠 DeepSeek Anti-Procrastination PM**: จัดคิวงานลูกค้า, แทรกงานด่วน, บังคับพักเที่ยง, และสรุปผลงานก่อนนอน 23:00 น.
3. **🩺 In-Charge Nurse Support**: จัดการเวรพยาบาล, มีปุ่มลัดแตะ 0.5 วินาที (จิบน้ำ/ของว่าง/ยุ่งมาก), เตือนแฟนซื้อของบำรุง
4. **🧾 Gemini Slip Vision OCR**: ส่งรูปสลิปโอนเงิน หรือใบเสร็จ 7-Eleven แกะยอดเงินลงบัญชีครัวเรือนอัตโนมัติ
5. **⏰ Celery Beat Routines**:
   - `07:30 น.` Morning Kickoff (ปลุกห้ามขึ้นเตียง + สรุปงานวันนี้)
   - `12:00 น.` Lunch Break (เตือนพักเที่ยง 1 ชม.)
   - `13:00 น.` Afternoon Kickoff (เรียกเริ่มงานบ่าย)
   - `15:00 น.` In-Charge Care (ส่งความห่วงใยรอบบ่าย)
   - `20:00 น.` Daily Expense Check-in (เช็กบิลค่าใช้จ่าย)
   - `23:00 น.` Night Work Review (ทวงสรุปงานคุณ)
   - `23:10 น.` Night Shift Question (ถามเวรแฟน)

---

## 🛠 วิธีติดตั้งและรันระบบ (Setup & Running)

### 1. ตั้งค่า `.env`
เปิดไฟล์ `.env` แล้วใส่ Token / API Keys:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
TELEGRAM_GROUP_ID="-100xxxxxxxxxx"
USER_TELEGRAM_ID="your_telegram_user_id"
PARTNER_TELEGRAM_ID="your_partner_telegram_user_id"

# AI Keys
DEEPSEEK_API_KEY="sk-..."
GROQ_API_KEY="gsk_..."
GEMINI_API_KEY="AIza..."
```

### 2. สั่งรันด้วย Docker Compose
รันคำสั่งเพียงคำสั่งเดียว ระบบจะสร้าง Database, Redis, Web Server, และ Celery Background Worker ให้ทั้งหมด:
```bash
docker compose up -d --build
```

### 3. ตรวจสอบสถานะการทำงาน
- ดูสถานะตู้คอนเทนเนอร์: `docker compose ps`
- ดู Log การทำงาน: `docker compose logs -f api`
- ตรวจสอบ API Documentation: เปิดเบราว์เซอร์ไปที่ `http://localhost:8000/docs`

### 4. เชื่อมต่อ Telegram Webhook
หากใช้ Cloudflare Tunnel หรือ Reverse Proxy (เช่น `https://my-home.example.com`):
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://my-home.example.com/api/v1/webhook/telegram"
```
