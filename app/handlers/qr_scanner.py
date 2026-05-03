import aiohttp
import asyncio
import logging
import os
from pyzbar.pyzbar import decode
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

PROVERKA_CHEKA_TOKEN = os.getenv("PROVERKA_CHEKA_TOKEN")

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor()

def sync_decode_qr(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        img.thumbnail((1024, 1024)) 
        decoded_objects = decode(img)
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
    except Exception as e:
        logger.error(f"Ошибка при чтении QR из {image_path}: {e}")
    return None

async def decode_qr(image_path: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_decode_qr, image_path)

async def fetch_receipt_data(qr_raw: str):
    url = "https://proverkacheka.com/api/v1/check/get"
    data = {
        "token": PROVERKA_CHEKA_TOKEN,
        "qrraw": qr_raw
    }
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ошибка API чеков. Статус: {response.status}")
                    return None
    except asyncio.TimeoutError:
        logger.warning("API чеков не ответил вовремя (Timeout)")
        return {"code": 0, "data": "Время ожидания истекло"}
    except Exception as e:
        logger.error(f"Сетевая ошибка при запросе к API чеков: {e}")
        return None