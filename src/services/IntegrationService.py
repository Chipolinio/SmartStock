import asyncio
import httpx
from datetime import date
from typing import List
from curl_cffi import requests
import re

API_BASE_URL = "http://127.0.0.1:8000"


def clean_for_pydantic(text: str, default: str = "Unknown") -> str:
    if not text or str(text).strip() == "":
        return default
    cleaned = re.sub(r'[^a-zA-Zа-яА-Я0-9\s\-\.\(\)\&№,\/\+]', '', str(text))
    result = cleaned.strip()
    return result if result else default


class WBScraper:
    def __init__(self):
        self.session = requests.Session(impersonate="safari15_5")

    async def get_articles_from_db(self) -> List[int]:
        # Возвращаем твой лимит, чтобы не было бесконечных запросов
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(f"{API_BASE_URL}/products/", params={"limit": 2500})
                if r.status_code == 200:
                    return [p["product_id"] for p in r.json()]
            except Exception as e:
                print(f"❌ Ошибка получения артикулов: {e}")
        return []

    def _transform(self, raw_data: List[dict]) -> dict:
        today = date.today().isoformat()
        payload = {
            "stocks": [],
            "prices": [],
            "deliveries": [],
            "socials": [],
            "products_update": []
        }

        for p in raw_data:
            pid = p.get("id")

            # 1. Сначала цена и фильтр аномалий
            price_info = p.get("sizes", [{}])[0].get("price", {})
            f_price = (price_info.get("product", 0) // 100) or 0

            # Пропускаем товар целиком, если цена аномальная,
            # чтобы не засирать статистику и не ломать Pydantic на бэке
            if f_price <= 0 or f_price > 500000:
                continue

            # 2. Метаданные
            clean_name = clean_for_pydantic(p.get("name", ""), default="Product " + str(pid))
            clean_brand = clean_for_pydantic(p.get("brand", ""), default="Generic")
            raw_entity = p.get("entity", "General")
            clean_subject = clean_for_pydantic(raw_entity, default="General")

            payload["products_update"].append({
                "product_id": pid,
                "name": clean_name[:200],
                "brand": clean_brand[:50] if clean_brand else "Generic",
                "subject": clean_subject,
                "entity": raw_entity
            })

            # 3. Остатки
            total_qty = 0
            for size in p.get("sizes", []):
                for wh in size.get("stocks", []):
                    total_qty += wh.get("qty", 0)

            # 4. Динамическая доставка (time1 + time2)
            t1 = p.get("time1", 0)
            t2 = p.get("time2", 0)
            delivery_days = max(1, (t1 + t2) // 24)

            payload["stocks"].append({"product_id": pid, "dt": today, "quantity": total_qty})
            payload["prices"].append({"product_id": pid, "dt": today, "price_sale": f_price, "discount_pct": 0})
            payload["deliveries"].append({"product_id": pid, "dt": today, "delivery_days": delivery_days})
            payload["socials"].append({
                "product_id": pid,
                "dt": today,
                "rating": float(p.get("reviewRating", 0)),
                "feedbacks": int(p.get("feedbacks", 0))
            })

        return payload

    async def run(self):
        articles = await self.get_articles_from_db()
        if not articles:
            print("База пуста.")
            return

        chunk_size = 100
        all_raw_products = []

        for i in range(0, len(articles), chunk_size):
            chunk = articles[i:i + chunk_size]
            nm_str = ";".join(map(str, chunk))
            url = f"https://card.wb.ru/cards/v4/detail?appType=1&curr=rub&dest=-1257786&nm={nm_str}"

            try:
                resp = self.session.get(url)
                if resp.status_code == 200:
                    products = resp.json().get("data", {}).get("products", [])
                    if not products:
                        products = resp.json().get("products", [])
                    all_raw_products.extend(products)
                print(f"Обработано артикулов: {len(all_raw_products)}")
            except Exception as e:
                print(f"Ошибка на чанке {i}: {e}")

        if not all_raw_products:
            print("WB ничего не вернул.")
            return

        payload = self._transform(all_raw_products)

        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{API_BASE_URL}/sales/full-payload", json=payload)
            print(f"Статус: {r.status_code}, Ответ: {r.text}")


if __name__ == "__main__":
    asyncio.run(WBScraper().run())