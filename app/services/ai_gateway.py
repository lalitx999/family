import io
import json
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIGateway:
    def __init__(self):
        # 1. DeepSeek Client (OpenAI SDK standard)
        self.deepseek_client = None
        if settings.DEEPSEEK_API_KEY:
            self.deepseek_client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL
            )

        # 2. Groq Client (OpenAI SDK standard for Whisper & Fast LLM)
        self.groq_client = None
        if settings.GROQ_API_KEY:
            self.groq_client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )

    # -------------------------------------------------------------
    # Groq: Whisper Voice Transcription (ไวสุดๆ ภาษาไทยแม่นยำ)
    # -------------------------------------------------------------
    async def transcribe_audio_groq(self, audio_bytes: bytes, filename: str = "voice.ogg") -> str:
        """แปลงเสียงพูดภาษาไทยจาก Telegram Voice Note เป็นข้อความในเสี้ยววินาที"""
        if not self.groq_client:
            logger.warning("GROQ_API_KEY is not configured.")
            return ""

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            transcription = await self.groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                language="th",
                temperature=0.0,
                response_format="text"
            )
            return str(transcription).strip()
        except Exception as e:
            logger.error(f"Error transcribing audio with Groq: {e}")
            return ""

    # -------------------------------------------------------------
    # DeepSeek: สมองหลัก Project Manager & Intent Classifier
    # -------------------------------------------------------------
    async def chat_deepseek(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """ส่งข้อความคุยกับ DeepSeek (PM ส่วนตัว สรุปงาน จัดการตารางชีวิต)"""
        if not self.deepseek_client:
            return "⚠️ ยังไม่ได้ตั้งค่า DEEPSEEK_API_KEY ในไฟล์ .env ครับ"

        try:
            response = await self.deepseek_client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {e}")
            return f"ขออภัยครับ เกิดข้อผิดพลาดในการเชื่อมต่อกับ DeepSeek: {e}"

    async def parse_intent_deepseek(self, user_message: str, sender_role: str = "freelancer") -> Dict[str, Any]:
        """
        ใช้ DeepSeek วิเคราะห์เจตนาของข้อความในกลุ่ม:
        - task_add: เพิ่มงานลูกค้า
        - task_urgent: มีงานด่วนแทรก
        - errand: ขอออกไปธุระ / พัก
        - shift_update: อัปเดตเวรแฟน
        - expense: บันทึกรายจ่าย
        - general_chat: คุยทั่วไป หรือตอบคำถาม
        """
        system_prompt = f"""
คุณคือ AI Project Manager และเลขาส่วนตัวของครอบครัว (Freelancer + แฟนพยาบาล)
หน้าที่ของคุณคือวิเคราะห์ข้อความจากผู้ใช้ (บทบาท: {sender_role}) แล้วสกัดข้อมูลเป็น JSON ตาม Schema ดังนี้:

JSON Schema:
{{
  "intent": "task_add" | "task_urgent" | "errand" | "shift_update" | "expense" | "general_chat",
  "data": {{
    "title": "ชื่องาน หรือ รายละเอียดธุระ (ถ้ามี)",
    "client_name": "ชื่อลูกค้า (ถ้ามี)",
    "priority": "urgent" | "high" | "normal" | "low",
    "amount": ตัวเลขยอดเงิน (ถ้าเป็น expense),
    "category": "food" | "transport" | "household" | "shopping" | "bills" | "other",
    "shift_type": "morning" | "afternoon" | "night" | "off" (ถ้าเป็น shift),
    "is_incharge": true | false (ถ้าเป็น shift ของแฟน)
  }},
  "reply_suggestion": "ข้อความตอบกลับสั้นๆ สไตล์ผู้ช่วยส่วนตัวที่เป็นกันเอง ตรงประเด็น ให้กำลังใจ"
}}

ตอบกลับเฉพาะ JSON เท่านั้น ห้ามมี Markdown หรือคำอธิบายเสริม
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        if not self.deepseek_client:
            return {"intent": "general_chat", "reply_suggestion": "ยังไม่ได้ตั้งค่า DeepSeek Key ครับ"}

        try:
            raw_res = await self.chat_deepseek(messages, temperature=0.1)
            # Remove ```json ... ``` wrapper if present
            cleaned = raw_res.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Error parsing intent with DeepSeek: {e}")
            return {
                "intent": "general_chat",
                "reply_suggestion": "รับทราบครับผม เดี๋ยวผมช่วยดูให้ครับ"
            }

    # -------------------------------------------------------------
    # Gemini: Multimodal Vision สำหรับสแกนสลิปโอนเงิน / ใบเสร็จ
    # -------------------------------------------------------------
    async def analyze_slip_gemini(self, image_bytes: bytes) -> Dict[str, Any]:
        """ใช้ Gemini 1.5/2.5 Flash อ่านรูปสลิปโอนเงิน / ใบเสร็จเซเว่น สกัดยอดเงินและหมวดหมู่"""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not configured.")
            return {"amount": 0, "category": "other", "note": "ยังไม่ได้ตั้งค่า GEMINI_API_KEY"}

        try:
            # We import google.genai here
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = """
จงวิเคราะห์ภาพสลิปโอนเงิน หรือ ใบเสร็จนี้ แล้วสกัดข้อมูลเป็น JSON ตามรูปแบบนี้เท่านั้น:
{
  "amount": ตัวเลขยอดเงิน (เช่น 120.50),
  "category": "food" | "transport" | "household" | "shopping" | "bills" | "medical" | "other",
  "note": "ชื่อร้านค้า หรือ บันทึกช่วยจำ เช่น ซื้อข้าวกะเพรา, 7-Eleven, โอนค่าเน็ต",
  "bank_or_store": "ชื่อธนาคารหรือร้านค้า"
}
ห้ามใส่ Markdown หรือข้อความอื่น ให้ส่ง JSON ล้วนๆ
"""
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg",
                    ),
                    prompt,
                ],
            )
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error analyzing slip with Gemini: {e}")
            return {"amount": 0, "category": "other", "note": "อ่านสลิปไม่สำเร็จ"}


ai_gateway = AIGateway()
