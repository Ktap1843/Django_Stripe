FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput || true
CMD ["gunicorn", "stripe_shop.wsgi:application", "--bind", "0.0.0.0:8000"]
