"""add exchange account sync metadata


Revision ID: 0002_exchange_account_sync_metadata
Revises: 0001_initial_stage1_schema
Create Date: 2026-06-16 01:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_exchange_account_sync_metadata"
down_revision = "0001_initial_stage1_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exchange_accounts", sa.Column("sync_status", sa.String(length=20), nullable=False, server_default="PENDING"))
    op.add_column("exchange_accounts", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("exchange_accounts", sa.Column("balance_snapshot", sa.JSON(), nullable=True))
    op.add_column("exchange_accounts", sa.Column("position_snapshot", sa.JSON(), nullable=True))
    op.add_column("exchange_accounts", sa.Column("error_message", sa.String(length=2000), nullable=True))


def downgrade() -> None:
    op.drop_column("exchange_accounts", "error_message")
    op.drop_column("exchange_accounts", "position_snapshot")
    op.drop_column("exchange_accounts", "balance_snapshot")
    op.drop_column("exchange_accounts", "last_synced_at")
    op.drop_column("exchange_accounts", "sync_status")
