.PHONY: install lint format test check

# Установить зависимости (включая lint и dev)
install:
	poetry install --with lint,dev

# Проверка стиля кода
lint:
	poetry run flake8 .
	poetry run mypy .

# Автоформатирование кода
format:
	poetry run black .
	poetry run isort .

# Запуск тестов с покрытием
test:
	poetry run pytest --cov=src --cov-report=term-missing

# Проверить всё: форматирование, линтинг, тесты
check: format lint test
