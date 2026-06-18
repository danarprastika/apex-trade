from __future__ import annotations

import csv
import io
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_trade_journal_service
from app.database.models.identity import User
from app.schemas.journal import (
    JournalAnalyticsSummary,
    JournalFilterParams,
    JournalListResponse,
    JournalStatistics,
    TagResponse,
    TradeJournalCreate,
    TradeJournalResponse,
    TradeJournalUpdate,
    TradeScreenshotResponse,
)
from app.services.journal_analytics_service import JournalAnalyticsService
from app.services.journal_search_service import journal_search_service
from app.services.trade_journal_service import TradeJournalService

router = APIRouter(prefix="/trades", tags=["journal_trades"])

CSV_FIELDS = [
    "journal_id",
    "trade_id",
    "strategy_id",
    "strategy_name",
    "entry_reason",
    "exit_reason",
    "notes",
    "lessons_learned",
    "risk_score",
    "outcome",
    "tags",
    "net_profit",
    "opened_at",
    "closed_at",
    "created_at",
]


@router.post("", response_model=TradeJournalResponse, status_code=201)
def create_journal_entry(
    payload: TradeJournalCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
):
    journal = service.create(current_user.id, payload)
    return journal


@router.get("/tags/autocomplete", response_model=list[TagResponse])
def autocomplete_tags(
    q: Annotated[str, Query(min_length=0)] = "",
    limit: Annotated[int, Query(le=50)] = 10,
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)] = None,
):
    return service.tags.autocomplete(q, limit)


@router.get("/stats/summary", response_model=JournalStatistics)
def get_summary_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
    filters: Annotated[JournalFilterParams, Query()] = None,
):
    return service.get_statistics(current_user.id, filters or JournalFilterParams())


@router.get("/stats/by-tag", response_model=dict[str, JournalStatistics])
def get_stats_by_tag(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
    filters: Annotated[JournalFilterParams, Query()] = None,
):
    return service.get_statistics_by_tag(current_user.id, filters or JournalFilterParams())


@router.get("/export/csv", include_in_schema=False)
def export_journal_csv(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
    filters: Annotated[JournalFilterParams, Query()] = None,
):
    rows = service.export_rows(current_user.id, filters or JournalFilterParams())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    headers = {
        "Content-Disposition": f"attachment; filename=trade-journals-{date.today().isoformat()}.csv"
    }
    output_str = output.getvalue()
    return StreamingResponse(iter([output_str]), media_type="text/csv", headers=headers)


@router.get("/analytics/performance-breakdown", response_model=JournalAnalyticsSummary)
def get_performance_breakdown(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[JournalFilterParams, Query()] = None,
):
    analytics = JournalAnalyticsService(db)
    filters = filters or JournalFilterParams()
    return JournalAnalyticsSummary(
        performance_breakdown=analytics.get_performance_breakdown(current_user.id, filters),
        risk_correlation=analytics.get_risk_correlation(current_user.id, filters),
        time_patterns=analytics.get_time_patterns(current_user.id, filters),
        tag_efficacy=analytics.get_tag_efficacy(current_user.id, filters),
    )


@router.get("/analytics/risk-correlation")
def get_risk_correlation(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[JournalFilterParams, Query()] = None,
):
    service = JournalAnalyticsService(db)
    return service.get_risk_correlation(current_user.id, filters or JournalFilterParams())


@router.get("/analytics/time-patterns")
def get_time_patterns(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[JournalFilterParams, Query()] = None,
):
    service = JournalAnalyticsService(db)
    return service.get_time_patterns(current_user.id, filters or JournalFilterParams())


@router.get("/analytics/tag-efficacy")
def get_tag_efficacy(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[JournalFilterParams, Query()] = None,
):
    service = JournalAnalyticsService(db)
    return service.get_tag_efficacy(current_user.id, filters or JournalFilterParams())


@router.get("/search", response_model=list[TradeJournalResponse])
def search_journals(
    q: Annotated[str, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(le=50)] = 20,
):
    results = journal_search_service.search(db, current_user.id, q, limit)
    for result in results:
        service.attach_related(result)
    return results


@router.post("/bulk-tag", status_code=204)
def bulk_tag_trades(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
    trade_ids: list[str] = Query(default_factory=list),
    tag_names: list[str] = Query(default_factory=list),
):
    service.bulk_tag(current_user.id, trade_ids, tag_names)
    return None


@router.get("", response_model=JournalListResponse)
def list_journals(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
    filters: Annotated[JournalFilterParams, Query()],
):
    items, total = service.list(current_user.id, filters)
    pages = (total + filters.size - 1) // filters.size
    return JournalListResponse(
        items=items,
        total=total,
        page=filters.page,
        size=filters.size,
        pages=pages,
    )


@router.get("/{journal_id}", response_model=TradeJournalResponse)
def get_journal_entry(
    journal_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
):
    journal = service.get(current_user.id, journal_id)
    return journal


@router.patch("/{journal_id}", response_model=TradeJournalResponse)
def update_journal_entry(
    journal_id: str,
    payload: TradeJournalUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
):
    journal = service.update(current_user.id, journal_id, payload)
    return journal


@router.delete("/{journal_id}", status_code=204)
def delete_journal_entry(
    journal_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
):
    service.delete(current_user.id, journal_id)
    return None


@router.post("/{journal_id}/screenshots", response_model=TradeScreenshotResponse, status_code=201)
def add_screenshot(
    journal_id: str,
    url: Annotated[str, Query()],
    caption: Annotated[str | None, Query()] = None,
    stage: Annotated[str | None, Query()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)] = None,
):
    screenshot = service.add_screenshot(current_user.id, journal_id, url, caption, stage)
    return screenshot


@router.delete("/{journal_id}/screenshots/{screenshot_id}", status_code=204)
def remove_screenshot(
    journal_id: str,
    screenshot_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TradeJournalService, Depends(get_trade_journal_service)],
):
    service.remove_screenshot(current_user.id, journal_id, screenshot_id)
    return None
