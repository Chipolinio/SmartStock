import json
import time
import re
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

API_BASE_URL = "http://127.0.0.1:8000"


def clean_text_for_api(text):
    if not text:
        return "Unknown"
    # Твой валидатор разрешает: буквы, цифры, пробелы, -, ., (), &, №, ,, /, +
    # Очищаем всё остальное, что не входит в этот список
    cleaned = re.sub(r'[^a-zA-Zа-яА-Я0-9\s\-\.\(\)\&№,\/\+]', '', str(text))
    return cleaned.strip()


def seed_to_db(products_data):
    if not products_data:
        print("⚠ Нечего отправлять в базу.")
        return

    unique_products = {p['product_id']: p for p in products_data}.values()
    payload = list(unique_products)

    try:
        print(f"🚀 Отправка {len(payload)} товаров на {API_BASE_URL}/products/bulk...")
        # Используем обычный httpx.post, так как сидер синхронный
        with httpx.Client(timeout=20.0) as client:
            response = client.post(f"{API_BASE_URL}/products/bulk", json=payload)

            if response.status_code in [200, 201]:
                print(f"✅ Успешно! База пополнена. Ответ: {len(response.json())} объектов.")
            else:
                # ВАЖНО: Выводим ответ API, чтобы увидеть ошибки валидации Pydantic
                print(f"🛑 Ошибка API {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка соединения с API: {e}")


def get_wildberries_and_seed(query="наушники"):
    print(f"🔎 Поиск на WB: {query}")
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}")
        time.sleep(4)

        # Тот самый эндпоинт v18
        api_url = f"https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?appType=1&curr=rub&dest=-1257786&query={query}&resultset=catalog&sort=popular&spp=30"

        driver.get(api_url)
        time.sleep(3)

        page_content = driver.page_source
        # Если открылся чистый JSON (pre-тег), забираем его текст
        if "pre" in page_content:
            page_content = driver.find_element("xpath", "//pre").text

        json_pattern = r'\{.*"products":\[.*\}'
        match = re.search(json_pattern, page_content, re.DOTALL)

        if match:
            data = json.loads(match.group(0))
            products = data.get('products', []) or data.get('data', {}).get('products', [])

            if not products:
                print("⚠ WB вернул пустой список товаров.")
                return

            to_create = []
            for p in products:
                # Очищаем данные строго под твой валидатор
                name = clean_text_for_api(p.get('name', ''))
                brand = clean_text_for_api(p.get('brand', ''))

                # Проверка на минимальную длину из твоей схемы [cite: 21, 24]
                if len(name) < 2: name = name + " Item"
                if len(brand) < 1: brand = "Generic"

                to_create.append({
                    "product_id": int(p.get('id')),
                    "brand": brand[:50],  # Ограничение из схемы [cite: 21, 24]
                    "name": name[:200],
                    "subject": clean_text_for_api(p.get('subjectName', 'General')),
                    "entity": "product"
                })

            print(f"📦 Подготовлено к заливке: {len(to_create)} товаров.")
            # ФИКС: Вызываем функцию отправки!
            seed_to_db(to_create)

        else:
            print("⚠ Не удалось извлечь JSON.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    queries = [
        "чай", "ноутбуки", "полотенца",
        "джинсы", "пальто", "книги",
        "ножи", "подушки", "колонки"
    ]
    for q in queries:
        get_wildberries_and_seed(q)
        time.sleep(10)
