# Django + Stripe

Тестовое задание: Django + Stripe API.  
Реализован бэкенд и простые HTML-страницы для покупки товаров через **Stripe Checkout**.  

## Features
- Django 5 + Stripe API
- Модель `Item` (товары)
- Модель `Order` с позициями (`OrderItem`)
- Поддержка скидок (`Discount`) и налогов (`Tax`)
- Разные валюты (EUR/USD), автоматическая конвертация в валюту заказа
- Stripe Checkout (Session API)
- Docker + PostgreSQL
- Seed demo data (`python manage.py seed_demo`)
- Тесты (pytest + pytest-django)
- CI (black, isort, flake8, pytest)

---

## Запуск локально

```bash
# подготовка окружения
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                                # !заполнить Stripe ключи!

# миграции + сидер
python manage.py migrate
python manage.py seed_demo

# старт сервера
python manage.py runserver
```

## Запуск в Docker
```bash
# собрать и запустить контейнеры
docker-compose build
docker-compose up -d

# миграции + сидер
docker-compose run --rm web python manage.py migrate
docker-compose run --rm web python manage.py seed_demo
```
## Тесты
```bash
pytest -q
docker-compose run --rm web sh -lc "pip install -r requirements-dev.txt"
```
## CI
Автоматическая проверка:
- black (форматирование)
- isort (импорты)
- flake8 (линтер)
- pytest (тесты)