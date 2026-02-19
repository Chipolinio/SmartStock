import asyncio
import re
from datetime import date
from typing import List
from curl_cffi import requests
from src.db.schemas.DataPack import FullPayload


def clean_for_pydantic(text: str, default: str = "Unknown") -> str:
    if not text or str(text).strip() == "":
        return default
    cleaned = re.sub(r'[^a-zA-Zа-яА-Я0-9\s\-\.\(\)\&№,\/\+]', '', str(text))
    result = cleaned.strip()
    return result if result else default


class WBScraper:
    def __init__(self):
        self.session = requests.Session(impersonate="safari15_5")

    def _transform(self, raw_data: List[dict]) -> FullPayload:
        today = date.today()
        payload = {
            "stocks": [],
            "prices": [],
            "deliveries": [],
            "socials": [],
            "products_update": []
        }

        for p in raw_data:
            pid = p.get("id")
            sizes = p.get("sizes", [])
            if not sizes:
                continue

            price_info = sizes[0].get("price", {})
            if not price_info:
                continue

            raw_product = price_info.get("product", 0)
            raw_basic = price_info.get("basic", 0)
            f_price = float(raw_product / 100)

            discount = price_info.get("sale")
            if discount is None:
                if raw_basic > raw_product and raw_basic > 0:
                    discount = int(((raw_basic - raw_product) / raw_basic) * 100)
                else:
                    discount = 0
            else:
                discount = int(discount)

            if pid == 248992051:
                print(f"!!! DEBUG ID {pid}: basic={raw_basic}, prod={raw_product}, calc_discount={discount}")

            if f_price <= 0 or f_price > 500000:
                continue

            clean_name = clean_for_pydantic(p.get("name", ""), default=f"Product {pid}")
            clean_brand = clean_for_pydantic(p.get("brand", ""), default="Generic")
            raw_entity = p.get("entity", "General")

            payload["products_update"].append({
                "product_id": pid,
                "name": clean_name[:200],
                "brand": clean_brand[:50],
                "subject": clean_for_pydantic(raw_entity, default="General"),
                "entity": raw_entity
            })

            total_qty = sum(wh.get("qty", 0) for size in p.get("sizes", []) for wh in size.get("stocks", []))
            t1, t2 = p.get("time1", 0), p.get("time2", 0)
            delivery_days = max(1, (t1 + t2) // 24)

            payload["stocks"].append({"product_id": pid, "dt": today, "quantity": total_qty})
            payload["prices"].append({
                "product_id": pid,
                "dt": today,
                "price_sale": f_price,
                "discount_pct": float(discount)
            })
            payload["deliveries"].append({"product_id": pid, "dt": today, "delivery_days": delivery_days})
            payload["socials"].append({
                "product_id": pid,
                "dt": today,
                "rating": float(p.get("reviewRating", 0)),
                "feedbacks": int(p.get("feedbacks", 0))
            })

        return FullPayload(**payload)

    async def fetch_data(self, articles: List[int]) -> FullPayload:
        chunk_size = 100
        all_raw_products = []

        for i in range(0, len(articles), chunk_size):
            chunk = articles[i:i + chunk_size]
            nm_str = ";".join(map(str, chunk))
            url = f"https://card.wb.ru/cards/v4/detail?appType=1&curr=rub&dest=-1257786&nm={nm_str}"

            try:
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, lambda: self.session.get(url))

                if resp.status_code == 200:
                    products = resp.json().get("data", {}).get("products", []) or resp.json().get("products", [])
                    all_raw_products.extend(products)
                print(f"📦 Скрапер: обработано артикулов {len(all_raw_products)}")
            except Exception as e:
                print(f"❌ Ошибка на чанке {i}: {e}")

        if not all_raw_products:
            raise ValueError("WB не вернул данных")

        return self._transform(all_raw_products)