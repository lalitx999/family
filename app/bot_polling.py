import asyncio
import logging
import httpx
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.api.v1.webhook import handle_incoming_message, handle_callback_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("bot_polling")


async def run_polling():
    """
    Long-polling runner สำหรับทดสอบหรือรันบน Home Server
    โดยไม่ต้องตั้งค่า Webhook หรือเปิดพอร์ตอินเทอร์เน็ต!
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is missing in .env")
        return

    # ลบ Webhook เก่าออกก่อนเพื่อให้ Polling ทำงานได้
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")

    logger.info("🤖 Starting Telegram Bot in Long-Polling mode...")
    offset = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=30"
            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    logger.warning(f"Failed to fetch updates: {res.text}")
                    await asyncio.sleep(2)
                    continue

                data = res.json()
                results = data.get("result", [])

                for item in results:
                    offset = item["update_id"] + 1

                    async with AsyncSessionLocal() as db:
                        # 1. Handle Callback Query
                        if "callback_query" in item:
                            await handle_callback_query(item["callback_query"], db)

                        # 2. Handle Message
                        if "message" in item:
                            await handle_incoming_message(item["message"], db)

        except asyncio.CancelledError:
            logger.info("Polling stopped.")
            break
        except Exception as e:
            logger.error(f"Polling loop error: {e}")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_polling())
