import logging
import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


class TelegramService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN is not configured.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    logger.error(f"Telegram send_message failed: {res.text}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error sending telegram message: {e}")
            return False

    async def send_group_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """ส่งข้อความเข้ากลุ่มหลัก (คุณ + แฟน + บอท)"""
        target = settings.TELEGRAM_GROUP_ID or settings.USER_TELEGRAM_ID
        if not target:
            logger.warning("No target chat ID configured for group message.")
            return False
        return await self.send_message(target, text, parse_mode, reply_markup)

    async def get_file_bytes(self, file_id: str) -> Optional[bytes]:
        """ดาวน์โหลดไฟล์ (เช่น รูปสลิป หรือ ไฟล์เสียง Voice Note) จาก Telegram"""
        if not self.bot_token:
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 1. getFile
                file_info_url = f"{self.base_url}/getFile?file_id={file_id}"
                res = await client.get(file_info_url)
                if res.status_code != 200:
                    return None
                file_path = res.json().get("result", {}).get("file_path")
                if not file_path:
                    return None

                # 2. Download file content
                download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                dl_res = await client.get(download_url)
                if dl_res.status_code == 200:
                    return dl_res.content
        except Exception as e:
            logger.error(f"Error downloading file from Telegram: {e}")
        return None


telegram_service = TelegramService()
