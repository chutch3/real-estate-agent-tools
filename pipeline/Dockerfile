FROM python:3.11-slim


WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root --without dev

COPY pipeline/ ./pipeline/
COPY regions/ ./regions/

RUN pip install --no-cache-dir --no-deps .
