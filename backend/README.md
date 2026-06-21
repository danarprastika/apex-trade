# QuantX Backend

FastAPI backend with Clean Architecture.

## Development

```bash
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```
