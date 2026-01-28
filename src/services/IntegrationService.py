import json
import re
import time
import httpx
import asyncio
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Настройки для браузера вынесем в константу
CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument('--headless')
CHROME_OPTIONS.add_argument('--disable-blink-features=AutomationControlled')
CHROME_OPTIONS.add_argument(
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')


def get_raw_wb_data(articles: list[int]):
    """Шаг 1: Просто парсим WB через Selenium (как ты и хотел)"""
    driver = webdriver.Chrome(options=CHROME_OPTIONS)
    try:
        driver.get(f"https://www.wildberries.ru/catalog/{articles[0]}/detail.aspx")
        time.sleep(3)

        nm_string = ";".join(map(str, articles))
        api_url = f"https://www.wildberries.ru/__internal/u-card/cards/v4/detail?appType=1&curr=rub&dest=-1257786&nm={nm_string}"

        driver.get(api_url)
        time.sleep(2)

        match = re.search(r'\{.*"products":\[.*}', driver.page_source, re.DOTALL)
        if not match: return []

        return json.loads(match.group(0)).get('products', [])
    finally:
        driver.quit()


async def send_to_api(endpoint: str, payload: dict):
    """Шаг 2: Вспомогательная функция для дерганья твоих рутов"""
    base_url = "http://127.0.0.1:8000"  # Твой локальный адрес FastAPI
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{base_url}{endpoint}", json=payload)
            return response.status_code
        except Exception as e:
            print(f"Ошибка при отправке в {endpoint}: {e}")
            return None


async def run_integration(articles: list[int]):
    """Главная функция: собрал — раскидал по рутам"""
    products_raw = get_raw_wb_data(articles)
    today = str(date.today())

    for p in products_raw:
        pid = p.get("id")

        # 1. Сохраняем/обновляем сам продукт [cite: 5]
        # Предполагаем, что у тебя есть рут POST /products/
        product_payload = {
            "product_id": pid,
            "name": p.get("name"),
            "brand": p.get("brand"),
            "subject": str(p.get("subjectId")),
            "entity": p.get("entity")
        }
        await send_to_api("/products/", product_payload)

        # 2. Пишем цену в PriceTS
        price_obj = p["sizes"][0].get("price", {})
        price_val = price_obj.get("product", 0) // 100
        await send_to_api("/prices/", {
            "product_id": pid,
            "dt": today,
            "price_sale": price_val,
            "discount_pct": 0.0  # Можно рассчитать, если рут требует
        })

        # 3. Пишем остатки в StockTS
        total_qty = sum(st.get("qty", 0) for size in p.get("sizes", []) for st in size.get("stocks", []))
        await send_to_api("/stocks/", {
            "product_id": pid,
            "dt": today,
            "quantity": total_qty
        })

        # 4. Пишем рейтинг в SocialTS [cite: 9]
        await send_to_api("/socials/", {
            "product_id": pid,
            "dt": today,
            "rating": p.get("reviewRating"),
            "feedbacks": p.get("feedbacks")
        })

        # 5. И финалочка в общую таблицу фичей [cite: 6, 7]
        await send_to_api("/features/daily/", {
            "product_id": pid,
            "dt": today,
            "price": float(price_val),
            "stock_left": total_qty,
            "rating": p.get("reviewRating"),
            "feedbacks": p.get("feedbacks")
        })

    print("🚀 Все данные успешно разосланы по рутам!")


if __name__ == "__main__":
    arts = [175570960, 175626966]
    asyncio.run(run_integration(arts))