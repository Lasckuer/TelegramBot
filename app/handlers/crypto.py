import aiohttp
import asyncio

async def get_live_rates():
    """Получает актуальные курсы валют и крипты к рублю"""
    rates = {'RUB': 1.0}
    
    fallback_rates = {
        'USD': 92.5, 
        'EUR': 99.0, 
        'BTC': 6000000.0, 
        'ETH': 300000.0, 
        'USDT': 92.5
    }

    timeout = aiohttp.ClientTimeout(total=5) 

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get("https://api.exchangerate-api.com/v4/latest/USD") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        usd_to_rub = data['rates'].get('RUB', fallback_rates['USD'])
                        eur_to_usd = data['rates'].get('EUR', 0.92)
                        
                        rates['USD'] = usd_to_rub
                        rates['EUR'] = usd_to_rub / eur_to_usd if eur_to_usd else fallback_rates['EUR']
                    else:
                        rates.update({'USD': fallback_rates['USD'], 'EUR': fallback_rates['EUR']})
            except Exception as e:
                print(f"Ошибка фиатного API: {e}")
                rates.update({'USD': fallback_rates['USD'], 'EUR': fallback_rates['EUR']})

            crypto_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether&vs_currencies=rub"
            try:
                async with session.get(crypto_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        rates['BTC'] = data.get('bitcoin', {}).get('rub', fallback_rates['BTC'])
                        rates['ETH'] = data.get('ethereum', {}).get('rub', fallback_rates['ETH'])
                        rates['USDT'] = data.get('tether', {}).get('rub', rates.get('USD', fallback_rates['USDT']))
                    else:
                        rates.update({'BTC': fallback_rates['BTC'], 'ETH': fallback_rates['ETH'], 'USDT': fallback_rates['USDT']})
            except Exception as e:
                print(f"Ошибка крипто API: {e}")
                rates.update({'BTC': fallback_rates['BTC'], 'ETH': fallback_rates['ETH'], 'USDT': fallback_rates['USDT']})
                
    except Exception as e:
        print(f"Общая ошибка сети в crypto.py: {e}")
        rates.update(fallback_rates)

    return rates