import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import AsyncSessionLocal
from src.db.schemas.Product import ProductCreate
from src.db.repositories.ProductRepositories import bulk_upsert_products


def clean_text_for_api(text):
    """Очистка текста от запрещённых символов."""
    if not text:
        return "Unknown"
    cleaned = re.sub(r'[^a-zA-Zа-яА-Я0-9\s\-\.\(\)\&№,\/\+]', '', str(text))
    return cleaned.strip()


def transform_products(raw_products: list[dict]) -> list[dict]:
    """
    Трансформация сырых данных WB в список словарей для ProductCreate.
    
    Args:
        raw_products: Сырые данные из API WB
        
    Returns:
        Список словарей для создания ProductCreate
    """
    to_create = []
    for p in raw_products:
        name = clean_text_for_api(p.get('name', ''))
        brand = clean_text_for_api(p.get('brand', ''))
        
        # Валидация минимальной длины
        if len(name) < 2:
            name = name + " Item"
        if len(brand) < 1:
            brand = "Generic"
        
        to_create.append({
            "product_id": int(p.get('id')),
            "brand": brand[:50],
            "name": name[:200],
            "subject": clean_text_for_api(p.get('subjectName', 'General')),
            "entity": "product"
        })
    
    return to_create


async def seed_to_db(products_data: list[dict], session: AsyncSession):
    """
    Сохранение товаров в БД напрямую через репозитории.
    
    Args:
        products_data: Список словарей с данными товаров
        session: Асинхронная сессия БД
        
    Returns:
        Список сохранённых товаров
    """
    if not products_data:
        print("⚠ Нечего отправлять в базу.")
        return []
    
    # Убираем дубликаты по product_id
    unique_products = {p['product_id']: p for p in products_data}.values()
    products_list = [ProductCreate(**p) for p in unique_products]
    
    try:
        print(f"🚀 Сохранение {len(products_list)} товаров через репозитории...")
        
        saved_products = await bulk_upsert_products(products_list, session)
        await session.commit()
        
        print(f"✅ Успешно! Сохранено: {len(saved_products)} товаров.")
        return saved_products
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Ошибка при сохранении: {e}")
        raise


async def seed_single_article(article: int, session: AsyncSession):
    """
    Добавить один товар по артикулу (заглушка).
    
    Args:
        article: Артикул WB
        session: Асинхронная сессия БД
        
    Returns:
        Список сохранённых товаров
    """
    products_data = [{
        "product_id": article,
        "name": f"Product {article}",
        "brand": "Unknown",
        "subject": "General",
        "entity": "product"
    }]
    return await seed_to_db(products_data, session)


async def seed_articles_batch(articles: list[int], session: AsyncSession):
    """
    Массовое добавление товаров по списку артикулов (заглушки).
    
    Args:
        articles: Список артикулов WB
        session: Асинхронная сессия БД
        
    Returns:
        Список сохранённых товаров
    """
    products_data = [
        {
            "product_id": article,
            "name": f"Product {article}",
            "brand": "Unknown",
            "subject": "General",
            "entity": "product"
        }
        for article in articles
    ]
    return await seed_to_db(products_data, session)


def get_wildberries_and_seed(query: str = "наушники"):
    """
    Поиск товаров на WB по запросу и сохранение в БД.
    
    Использует Selenium для получения данных из внутреннего API WB.
    
    Args:
        query: Поисковый запрос
    """
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

        api_url = f"https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?appType=1&curr=rub&dest=-1257786&query={query}&resultset=catalog&sort=popular&spp=30"

        driver.get(api_url)
        time.sleep(3)

        page_content = driver.page_source
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

            # Трансформируем в словари
            to_create = transform_products(products)
            print(f"📦 Подготовлено к заливке: {len(to_create)} товаров.")
            
            # Сохраняем напрямую через репозитории (без API!)
            import asyncio
            async def _save():
                async with AsyncSessionLocal() as session:
                    await seed_to_db(to_create, session)
            
            asyncio.run(_save())

        else:
            print("⚠ Не удалось извлечь JSON.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    queries = [
        "клавиатура", "мышь компьютерная", "кофе",
        "штаны", "чехол", "смартфон",
        "чайник", "носки", "ковер"
    ]

    for q in queries:
        get_wildberries_and_seed(q)
        time.sleep(10)
