import asyncio
from curl_cffi.requests import AsyncSession


async def get_popular_now():
    # Эндпоинт электроники (одна из самых больших категорий)
    # Используем v4 - он самый стабильный
    url = "https://catalog.wb.ru/catalog/electronic2/v4/catalog?appType=1&cat=611&curr=rub&dest=-1257786&sort=popular&spp=30"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Referer": "https://www.wildberries.ru/"
    }

    # Используем chrome110 - он поддерживается во всех версиях curl_cffi
    async with AsyncSession(impersonate="chrome110") as session:
        try:
            print("📡 Попытка пробиться через стабильный каталог (Chrome 110)...")
            response = await session.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])

                if not products:
                    print("😕 WB прислал пустой список. Возможно, нужно сменить dest (регион).")
                    return

                print(f"✅ УСПЕХ! Найдено {len(products)} артикулов.")

                # Формируем данные для твоей БД
                to_seed = []
                for p in products[:100]:  # Берем первые 100 штук
                    to_seed.append({
                        "product_id": p.get("id"),
                        "name": p.get("name"),
                        "brand": p.get("brand"),
                        "subject": p.get("subjectName"),
                        "entity": "product"
                    })

                for item in to_seed[:5]:
                    print(f"🔹 Артикул: {item['product_id']} | {item['name']}")

                print(f"\n🚀 Теперь можешь отправлять эти {len(to_seed)} объектов в свой API /products/bulk")

            elif response.status_code == 429:
                print("🛑 429: Твой IP все еще в бане. Смени интернет (мобильная точка) или подожди 15 мин.")
            else:
                print(f"❌ Ошибка {response.status_code}. Ответ сервера: {response.text[:100]}")

        except Exception as e:
            print(f"💥 Ошибка при выполнении запроса: {e}")


if __name__ == "__main__":
    asyncio.run(get_popular_now())