import aiohttp
import asyncio
import json
from pyzbar.pyzbar import decode
from PIL import Image
from config import PROVERKA_CHEKA_TOKEN

def decode_qr(image_path: str) -> str:
    """Извлекает текст (строку ФНС) из QR-кода на фото."""
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
    except Exception as e:
        print(f"Ошибка при чтении QR: {e}")
    return None

async def fetch_receipt_data(qr_raw: str):
    """Отправляет запрос к API proverkacheka.com и возвращает JSON."""
    
    # 👇 ИСПРАВЛЕННЫЙ АДРЕС САЙТА (БЕЗ ДЕФИСА) 👇
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
                    text_data = await response.text()
                    try:
                        return json.loads(text_data)
                    except json.JSONDecodeError:
                        print("Ошибка: API вернул не JSON.")
                        return {"code": -1, "error": "Неверный ответ от сервера API."}
                else:
                    print(f"Ошибка API. Статус код: {response.status}")
                    return None
    except asyncio.TimeoutError:
        print("Ошибка: Превышено время ожидания ответа от API.")
        return None
    except Exception as e:
        print(f"Сетевая ошибка: {e}")
        return None