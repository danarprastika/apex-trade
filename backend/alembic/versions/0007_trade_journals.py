"""trade journal tables

Revision ID: 0007_trade_journals
Revises: 0006_portfolio_analytics
Create Date: 2026-06-18

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0007_trade_journals"
down_revision = "0006_portfolio_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trade_journals",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("trade_id", sa.String(length=36), sa.ForeignKey("trades.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("signals.id"), nullable=True),
        sa.Column("strategy_id", sa.String(length=36), sa.ForeignKey("strategies.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entry_reason", sa.Text(), nullable=False),
        sa.Column("exit_reason", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("risk_score", sa.SmallInteger(), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("search_vector", sa.dialects.postgresql.tsvector(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("trade_id", name="uq_trade_journals_trade_id"),
    )
    op.create_index("ix_trade_journals_user_id", "trade_journals", ["user_id"])
    op.create_index("ix_trade_journals_strategy_id", "trade_journals", ["strategy_id"])
    op.create_index("ix_trade_journals_outcome", "trade_journals", ["outcome"])
    op.create_index("ix_trade_journals_created_at", "trade_journals", ["created_at"])
    op.create_index("ix_trade_journals_deleted_at", "trade_journals", ["deleted_at"])
    op.create_index("ix_trade_journals_user_strategy", "trade_journals", ["user_id", "strategy_id", "created_at"])
    op.create_index(
        "ix_trade_journals_search",
        "trade_journals",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.execute(
        """
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON trade_journals
        FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(search_vector, 'pg_catalog.english',
            entry_reason, exit_reason, notes, lessons_learned)
        """
    )

    op.create_table(
        "trade_screenshots",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("trade_journal_id", sa.String(length=36), sa.ForeignKey("trade_journals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.String(length=200), nullable=True),
        sa.Column("stage", sa.String(length=20), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_trade_screenshots_journal_id", "trade_screenshots", ["trade_journal_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#6B7280"),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("name", name="uq_tags_name"),
    )
    op.create_index("ix_tags_name", "tags", ["name"])

    op.create_table(
        "trade_tag_relations",
        sa.Column("trade_journal_id", sa.String(length=36), sa.ForeignKey("trade_journals.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(length=36), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "journal_enrichments",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("trade_journal_id", sa.String(length=36), sa.ForeignKey("trade_journals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enrichment_type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_journal_enrichments_journal_id", "journal_enrichments", ["trade_journal_id"])


def downgrade() -> None:
    op.drop_index("ix_journal_enrichments_journal_id", table_name="journal_enrichments")
    op.drop_table("journal_enrichments")
    op.drop_table("trade_tag_relations")
    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_table("tags")
    op.drop_index("ix_trade_screenshots_journal_id", table_name="trade_screenshots")
    op.drop_table("trade_screenshots")
    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate ON trade_journals")
    op.drop_index("ix_trade_journals_search", table_name="trade_journals")
    op.drop_index("ix_trade_journals_user_strategy", table_name="trade_journals")
    op.drop_index("ix_trade_journals_deleted_at", table_name="trade_journals")
    op.drop_index("ix_trade_journals_created_at", table_name="trade_journals")
    op.drop_index("ix_trade_journals_outcome", table_name="trade_journals")
    op.drop_index("ix_trade_journals_strategy_id", table_name="trade_journals")
    op.drop_index("ix_trade_journals_user_id", table_name="trade_journals")
    op.drop_table("trade_journals")
