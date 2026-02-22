import pytest
from datetime import date
from src.services.IntegrationService import WBScraper, clean_for_pydantic


def test_clean_for_pydantic_logic():
    assert clean_for_pydantic("Кеды (синие) !!!") == "Кеды (синие)"
    assert clean_for_pydantic("  ") == "Unknown"
    assert clean_for_pydantic(None) == "Unknown"
    assert clean_for_pydantic("Кофе №1", default="Empty") == "Кофе №1"


def test_scraper_transform_success():
    scraper = WBScraper()
    today = date.today()

    raw_data = [{
        "id": 100,
        "name": " Смартфон X ",
        "brand": "Brand Y",
        "entity": "smartphones",
        "time1": 12,
        "time2": 36,
        "reviewRating": 4.5,
        "feedbacks": 100,
        "sizes": [{
            "price": {"product": 5000000},
            "stocks": [{"qty": 5}, {"qty": 10}]
        }]
    }]

    payload = scraper._transform(raw_data)

    assert len(payload.products_update) == 1
    assert payload.products_update[0].name == "Смартфон X"
    assert payload.products_update[0].brand == "Brand Y"
    assert payload.products_update[0].product_id == 100

    assert payload.prices[0].price_sale == 50000.0
    assert payload.prices[0].dt == today

    assert payload.deliveries[0].delivery_days == 2

    assert payload.stocks[0].quantity == 15
    assert payload.stocks[0].dt == today

    assert payload.socials[0].rating == 4.5
    assert payload.socials[0].feedbacks == 100


@pytest.mark.parametrize("bad_price", [0, -100, 60000000])
def test_scraper_transform_anomaly_filter(bad_price):
    scraper = WBScraper()
    raw_data = [{
        "id": 999,
        "sizes": [{"price": {"product": bad_price * 100}}]
    }]

    payload = scraper._transform(raw_data)

    assert len(payload.prices) == 0
    assert len(payload.stocks) == 0
    assert len(payload.products_update) == 0


def test_scraper_transform_empty_data():
    scraper = WBScraper()
    payload = scraper._transform([])

    data_dict = payload.model_dump()
    for key, value in data_dict.items():
        assert value == [] or value is None


@pytest.mark.asyncio
async def test_scraper_run_network_errors(mocker):
    scraper = WBScraper()
    mocker.patch.object(scraper.session, "get", side_effect=Exception("Network error"))

    with pytest.raises(ValueError, match="WB не вернул данных"):
        await scraper.fetch_data([123, 456])


def test_scraper_transform_broken_json():
    scraper = WBScraper()
    broken_raw_data = [{
        "id": 555,
        "sizes": [
            {
                "price": {"product": 10000},
                "stocks": [{"qty": 10}]
            }
        ],
        "time1": 10
    }]

    payload = scraper._transform(broken_raw_data)

    assert len(payload.products_update) == 1
    product = payload.products_update[0]

    assert product.product_id == 555
    assert product.name == "Product 555"
    assert product.brand == "Generic"
    assert product.subject == "General"

    assert payload.prices[0].price_sale == 100.0
    assert payload.deliveries[0].delivery_days == 1


def test_scraper_transform_partial_broken():
    scraper = WBScraper()
    raw_data = [
        {"id": 1, "name": "Good", "sizes": [{"price": {"product": 10000}, "stocks": []}]},
        {"id": 2, "name": "Bad", "sizes": [{"price": {"product": 0}, "stocks": []}]}
    ]

    payload = scraper._transform(raw_data)

    assert len(payload.products_update) == 1
    assert payload.products_update[0].product_id == 1