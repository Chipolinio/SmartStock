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
    today = date.today().isoformat()

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

    assert len(payload["products_update"]) == 1
    assert payload["products_update"][0]["name"] == "Смартфон X"
    assert payload["prices"][0]["price_sale"] == 50000

    assert payload["deliveries"][0]["delivery_days"] == 2

    assert payload["stocks"][0]["quantity"] == 15
    assert payload["stocks"][0]["dt"] == today


@pytest.mark.parametrize("bad_price", [0, -100, 60000000])
def test_scraper_transform_anomaly_filter(bad_price):
    scraper = WBScraper()
    raw_data = [{
        "id": 999,
        "sizes": [{"price": {"product": bad_price * 100}}]
    }]

    payload = scraper._transform(raw_data)

    assert len(payload["prices"]) == 0
    assert len(payload["stocks"]) == 0
    assert len(payload["products_update"]) == 0


def test_scraper_transform_empty_data():
    scraper = WBScraper()
    payload = scraper._transform([])

    for key in payload:
        assert payload[key] == []