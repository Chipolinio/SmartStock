import asyncio
import httpx
from datetime import date
from typing import List
from curl_cffi import requests

API_BASE_URL = "http://127.0.0.1:8000"


class WBScraper:
    def __init__(self):
        self.session = requests.Session(impersonate="safari15_5")

    async def get_articles_from_db(self) -> List[int]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(f"{API_BASE_URL}/products/", params={"limit": 1000})
                if r.status_code == 200:
                    return [p["product_id"] for p in r.json()]
            except Exception as e:
                print(f"❌ Ошибка получения артикулов: {e}")
        return []

    def _transform(self, raw_data: List[dict]) -> dict:
        today = date.today().isoformat()
        # Структура строго под твою схему FullPayload
        payload = {
            "stocks": [],
            "prices": [],
            "deliveries": [],
            "socials": [],
            "sales": []  # Optional в схеме
        }

        for p in raw_data:
            pid = p.get("id")

            # ЧЕСТНЫЙ РАСЧЕТ QTY (по всем размерам и складам)
            total_qty = 0
            for size in p.get("sizes", []):
                for wh in size.get("stocks", []):
                    total_qty += wh.get("qty", 0)

            # ЦЕНА
            price_info = p.get("sizes", [{}])[0].get("price", {})
            f_price = price_info.get("product", 0) // 100
            orig_price = price_info.get("basic", 0) // 100
            disc = round((1 - (f_price / orig_price)) * 100, 2) if orig_price > 0 else 0

            # Данные для FullPayload
            payload["stocks"].append({"product_id": pid, "dt": today, "quantity": total_qty})
            payload["prices"].append(
                {"product_id": pid, "dt": today, "price_sale": f_price, "discount_pct": float(disc)})
            payload["deliveries"].append({"product_id": pid, "dt": today, "delivery_days": 1})  # Заглушка
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

        # Тянем данные с WB
        nm_str = ";".join(map(str, articles))
        url = f"https://card.wb.ru/cards/v4/detail?appType=1&curr=rub&dest=-1257786&nm={nm_str}"

        resp = self.session.get(url)
        if resp.status_code == 200:
            raw_products = resp.json().get("products", [])
            payload = self._transform(raw_products)

            # Отправка
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.post(f"{API_BASE_URL}/sales/full-payload", json=payload)
                print(f"Статус: {r.status_code}, Ответ: {r.text}")


if __name__ == "__main__":
    asyncio.run(WBScraper().run())