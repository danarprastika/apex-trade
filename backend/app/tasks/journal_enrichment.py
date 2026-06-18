from __future__ import annotations

from app.database.repositories.journal_repository import (
    JournalEnrichmentRepository,
    TradeJournalRepository,
)
from app.database.repositories.trading_repository import SignalRepository, TradeRepository
from app.database.session import SessionLocal
from app.services.journal_ai_service import JournalAIService
from app.tasks.celery_app import celery_app


@celery_app.task(name="journal.enrich_journal", bind=True)
def enrich_journal(self, journal_id: str) -> dict[str, object]:
    db = SessionLocal()
    try:
        journal = TradeJournalRepository(db).get(journal_id)
        if not journal:
            return {"status": "not_found", "journal_id": journal_id}

        trade = TradeRepository(db).get(journal.trade_id)
        signal = SignalRepository(db).get(journal.signal_id) if journal.signal_id else None
        enrichments = JournalAIService.build_enrichments(journal, trade, signal)
        enrichment_repo = JournalEnrichmentRepository(db)
        persisted = []

        for item in enrichments:
            enrichment = enrichment_repo.create(**item)
            persisted.append(
                {
                    "id": enrichment.id,
                    "enrichment_type": enrichment.enrichment_type,
                    "confidence": float(enrichment.confidence)
                    if enrichment.confidence is not None
                    else None,
                }
            )

        db.commit()
        return {"status": "ok", "journal_id": journal_id, "enrichments": persisted}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
