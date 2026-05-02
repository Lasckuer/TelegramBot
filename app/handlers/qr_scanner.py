import aiohttp
import asyncio
import json
from pyzbar.pyzbar import decode
from PIL import Image
from app.config import PROVERKA_CHEKA_TOKEN
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

def sync_decode_qr(image_path: str) -> str:
    """Синхронная функция декодирования (блокирует поток)"""
    try:
        img = Image.open(image_path)
        img.thumbnail((1024, 1024)) 
        decoded_objects = decode(img)
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
    except Exception as e:
        print(f"Ошибка при чтении QR: {e}")
    return None

async def decode_qr(image_path: str):
    """Асинхронная обертка: запускает декодирование в отдельном потоке"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_decode_qr, image_path)

async def fetch_receipt_data(qr_raw: str):
    """Отправляет запрос к API proverkacheka.com"""
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
                    print(f"Ошибка API. Статус: {response.status}")
                    return None
    except asyncio.TimeoutError:
        print("Ошибка: API чеков не ответил вовремя.")
        return {"code": 0, "data": "Время ожидания истекло"}
    except Exception as e:
        print(f"Сетевая ошибка: {e}")
        return None