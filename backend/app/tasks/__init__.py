__all__ = ["enrich_journal"]


def __getattr__(name: str):
    if name == "enrich_journal":
        from app.tasks.journal_enrichment import enrich_journal

        return enrich_journal
    raise AttributeError(name)
