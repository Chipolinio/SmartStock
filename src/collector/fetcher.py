import json
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_wildberries_working_version(query="наушники"):
    print(f"🚀 Запуск проверенного метода для: {query}")

    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options)

    try:
        print("🏠 Шаг 1: Прогрев сессии...")
        driver.get(f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}")
        time.sleep(5)

        api_url = f"https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-364763&query={query}&resultset=catalog&sort=popular&spp=30"
        print(f"📡 Шаг 2: Переход на API...")
        driver.get(api_url)
        time.sleep(5)

        page_content = driver.page_source

        if "429" in page_content and len(page_content) < 500:
            print("❌ Ошибка 429: WB всё-таки заблокировал запрос. Попробуй сменить IP.")
            return

        print("🔍 Вырезаем JSON из верстки...")
        json_pattern = r'\{.*"products":\[.*\}'
        match = re.search(json_pattern, page_content, re.DOTALL)

        if match:
            json_text = match.group(0)

            with open('wb_raw_data.json', 'w', encoding='utf-8') as f:
                f.write(json_text)

            data = json.loads(json_text)
            products = data.get('products', [])

            if not products:
                products = data.get('data', {}).get('products', [])

            print(f"✅ Успех! Найдено товаров: {len(products)}")

            items = []
            for p in products:
                price = 0
                if p.get("sizes"):
                    price_raw = p["sizes"][0].get("price", {}).get("product", 0)
                    price = price_raw / 100

                items.append({
                    "ID": p.get('id'),
                    "Бренд": p.get('brand'),
                    "Название": p.get('name'),
                    "Цена (руб)": price,
                    "Рейтинг": p.get('reviewRating'),
                    "Отзывов": p.get('feedbacks'),
                    "Категория": p.get('entity')
                })

            df = pd.DataFrame(items)
            df.to_excel('wildberries_results.xlsx', index=False)
            df.to_csv('wildberries_results.csv', index=False, encoding='utf-8-sig')

            print("\n💾 Сохранено в .xlsx и .csv!")
            print(df.head())
        else:
            print("⚠ JSON не найден. Возможно, страница пустая или структура изменилась.")
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(page_content)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        print("🔄 Выход...")
        driver.quit()


if __name__ == "__main__":
    get_wildberries_working_version("наушники")