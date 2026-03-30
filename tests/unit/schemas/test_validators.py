"""
Юнит-тесты для schemas и validators (функциональный подход).

Тестируемые функции:
- validate_email_strict() — валидация email
- validate_clean_text() — валидация текста
- validate_strict_date() — валидация даты
- extract_article() — извлечение артикула
"""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from src.utils.validators import (
    validate_email_strict,
    validate_clean_text,
    validate_strict_date,
    extract_article,
)


class TestValidateEmailStrict:
    """Тесты валидации email."""

    def test_valid_email_simple(self):
        """Валидный простой email."""
        # Arrange
        email = "test@example.com"

        # Act
        result = validate_email_strict(email)

        # Assert
        assert result == "test@example.com"

    def test_valid_email_with_dots(self):
        """Валидный email с точками."""
        # Arrange
        email = "test.user@example.com"

        # Act
        result = validate_email_strict(email)

        # Assert
        assert result == "test.user@example.com"

    def test_valid_email_with_plus(self):
        """Валидный email с плюсом."""
        # Arrange
        email = "test+user@example.com"

        # Act
        result = validate_email_strict(email)

        # Assert
        assert result == "test+user@example.com"

    def test_valid_email_trimmed(self):
        """Валидный email обрезается."""
        # Arrange
        email = "  TEST@EXAMPLE.COM  "

        # Act
        result = validate_email_strict(email)

        # Assert
        assert result == "test@example.com"  # Приводится к нижнему регистру

    def test_invalid_email_no_at(self):
        """Невалидный email без @."""
        # Arrange
        email = "testexample.com"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email_strict(email)

    def test_invalid_email_no_domain(self):
        """Невалидный email без домена."""
        # Arrange
        email = "test@"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email_strict(email)

    def test_invalid_email_no_tld(self):
        """Невалидный email без TLD."""
        # Arrange
        email = "test@example"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email_strict(email)

    def test_invalid_email_short_tld(self):
        """Невалидный email с коротким TLD."""
        # Arrange
        email = "test@example.c"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email_strict(email)

    def test_invalid_email_empty(self):
        """Невалидный пустой email."""
        # Arrange
        email = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email_strict(email)

    def test_invalid_email_spaces(self):
        """Невалидный email с пробелами внутри."""
        # Arrange
        email = "test @example.com"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email_strict(email)


class TestValidateCleanText:
    """Тесты валидации текста."""

    def test_valid_text_simple(self):
        """Валидный простой текст."""
        # Arrange
        text = "Hello World"

        # Act
        result = validate_clean_text(text)

        # Assert
        assert result == "Hello World"

    def test_valid_text_with_numbers(self):
        """Валидный текст с цифрами."""
        # Arrange
        text = "Product 123"

        # Act
        result = validate_clean_text(text)

        # Assert
        assert result == "Product 123"

    def test_valid_text_with_allowed_special_chars(self):
        """Валидный текст с разрешенными спецсимволами."""
        # Arrange
        text = "Test-Product (123) & More, №1"

        # Act
        result = validate_clean_text(text)

        # Assert
        assert result == "Test-Product (123) & More, №1"

    def test_valid_text_trimmed(self):
        """Валидный текст обрезается."""
        # Arrange
        text = "  Hello World  "

        # Act
        result = validate_clean_text(text)

        # Assert
        assert result == "Hello World"

    def test_invalid_text_empty(self):
        """Невалидный пустой текст."""
        # Arrange
        text = ""

        # Act & Assert
        with pytest.raises(ValueError, match="empty"):
            validate_clean_text(text)

    def test_invalid_text_none(self):
        """Невалидный None текст."""
        # Arrange
        text = None

        # Act & Assert
        with pytest.raises(ValueError, match="empty"):
            validate_clean_text(text)

    def test_invalid_text_whitespace_only(self):
        """Невалидный текст только с пробелами."""
        # Arrange
        text = "   "

        # Act & Assert
        with pytest.raises(ValueError, match="empty"):
            validate_clean_text(text)

    def test_invalid_text_too_short(self):
        """Невалидный текст короче 2 символов."""
        # Arrange
        text = "A"

        # Act & Assert
        with pytest.raises(ValueError, match="at least 2"):
            validate_clean_text(text)

    def test_invalid_text_forbidden_chars(self):
        """Невалидный текст с запрещенными символами."""
        # Arrange
        text = "Hello <World>"

        # Act & Assert
        with pytest.raises(ValueError, match="prohibited"):
            validate_clean_text(text)

    def test_invalid_text_with_quotes(self):
        """Невалидный текст с кавычками."""
        # Arrange
        text = 'Hello "World"'

        # Act & Assert
        with pytest.raises(ValueError, match="prohibited"):
            validate_clean_text(text)


class TestValidateStrictDate:
    """Тесты валидации даты."""

    def test_valid_date_today(self):
        """Валидная дата - сегодня."""
        # Arrange
        test_date = date.today()

        # Act
        result = validate_strict_date(test_date)

        # Assert
        assert result == test_date

    def test_valid_date_past(self):
        """Валидная дата в прошлом."""
        # Arrange
        test_date = date.today() - timedelta(days=30)

        # Act
        result = validate_strict_date(test_date)

        # Assert
        assert result == test_date

    def test_valid_date_old(self):
        """Валидная старая дата (после 2010)."""
        # Arrange
        test_date = date(2020, 1, 1)

        # Act
        result = validate_strict_date(test_date)

        # Assert
        assert result == test_date

    def test_invalid_date_future(self):
        """Невалидная дата в будущем."""
        # Arrange
        test_date = date.today() + timedelta(days=1)

        # Act & Assert
        with pytest.raises(ValueError, match="future"):
            validate_strict_date(test_date)

    def test_invalid_date_too_old(self):
        """Невалидная слишком старая дата."""
        # Arrange
        test_date = date(2009, 12, 31)

        # Act & Assert
        with pytest.raises(ValueError, match="past"):
            validate_strict_date(test_date)

    def test_invalid_date_none(self):
        """Невалидная None дата."""
        # Arrange
        test_date = None

        # Act & Assert
        with pytest.raises(ValueError, match="required"):
            validate_strict_date(test_date)

    def test_invalid_date_string(self):
        """Невалидная строка вместо даты."""
        # Arrange
        test_date = "2026-03-29"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_strict_date(test_date)


class TestExtractArticle:
    """Тесты извлечения артикула."""

    def test_extract_article_simple(self):
        """Извлечение простого артикула."""
        # Arrange
        text = "12345678"

        # Act
        result = extract_article(text)

        # Assert
        assert result == 12345678

    def test_extract_article_from_text(self):
        """Извлечение артикула из текста."""
        # Arrange
        text = "Артикул товара: 123456789"

        # Act
        result = extract_article(text)

        # Assert
        assert result == 123456789

    def test_extract_article_with_at_sign(self):
        """Возврат None если есть @."""
        # Arrange
        text = "@12345678"

        # Act
        result = extract_article(text)

        # Assert
        assert result is None

    def test_extract_article_no_digits(self):
        """Возврат None если нет цифр."""
        # Arrange
        text = "abcdefg"

        # Act
        result = extract_article(text)

        # Assert
        assert result is None

    def test_extract_article_short_digits(self):
        """Возврат None если цифры короче 5 символов."""
        # Arrange
        text = "1234"

        # Act
        result = extract_article(text)

        # Assert
        assert result is None

    def test_extract_article_first_match(self):
        """Извлечение первого совпадения."""
        # Arrange
        text = "Товар 12345678 и 987654321"

        # Act
        result = extract_article(text)

        # Assert
        assert result == 12345678

    def test_extract_article_long_number(self):
        """Извлечение длинного числа (до 12 цифр)."""
        # Arrange
        text = "123456789012"

        # Act
        result = extract_article(text)

        # Assert
        assert result == 123456789012
