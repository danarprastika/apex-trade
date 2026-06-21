FROM python:3.12-slim AS builder

WORKDIR /app

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install -e ".[dev]"

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY backend/app ./app/

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
