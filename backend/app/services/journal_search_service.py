from __future__ import annotations

from typing import Any

from sqlalchemy import true
from sqlalchemy.dialects.postgresql import to_tsquery
from sqlalchemy.orm import Session


def build_search_vector_filter(search_vector, query: str):
    cleaned = query.strip().replace("'", " ")
    if not cleaned or search_vector is None:
        return true()

    terms = []
    for token in cleaned.split():
        token = token.strip()
        if token:
            terms.append(f"{token}:*")

    ts_query_string = " & ".join(terms) if terms else None
    if not ts_query_string:
        return true()

    return search_vector.op("@@")(to_tsquery("english", ts_query_string))


class JournalSearchService:
    def search(self, db: Session, user_id: str, query: str, limit: int = 20) -> list[Any]:
        from app.database.repositories.journal_repository import TradeJournalRepository

        return TradeJournalRepository(db).search(user_id, query, limit)


journal_search_service = JournalSearchService()
