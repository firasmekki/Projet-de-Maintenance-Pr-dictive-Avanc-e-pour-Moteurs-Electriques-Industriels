"""add analysis_reports table

Revision ID: 0003_add_analysis_reports
Revises: 0002_add_prediction_history
Create Date: 2026-06-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_analysis_reports"
down_revision: str | None = "0002_add_prediction_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_reports",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("column_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_values", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="uploaded"),
        sa.Column("columns_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("dataset_json", sa.Text(), nullable=True),
        sa.Column("analysis_json", sa.Text(), nullable=True),
        sa.Column("ai_narrative", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_reports_created_at", "analysis_reports", ["created_at"])
    op.create_index("ix_analysis_reports_status", "analysis_reports", ["status"])


def downgrade() -> None:
    op.drop_index("ix_analysis_reports_status", table_name="analysis_reports")
    op.drop_index("ix_analysis_reports_created_at", table_name="analysis_reports")
    op.drop_table("analysis_reports")
