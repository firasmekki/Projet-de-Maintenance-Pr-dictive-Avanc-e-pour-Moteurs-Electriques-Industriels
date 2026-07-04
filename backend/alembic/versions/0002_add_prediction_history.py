"""add prediction_history table

Revision ID: 0002_add_prediction_history
Revises: 0001_create_core_tables
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002_add_prediction_history"
down_revision: str | None = "0001_create_core_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prediction_history",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("motor_id", sa.Uuid(as_uuid=True), nullable=False),
        # Fault classification
        sa.Column("predicted_fault", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        # Health
        sa.Column("health_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("health_status", sa.String(20), nullable=False),
        # Risk horizons
        sa.Column("risk_score_7d", sa.Numeric(8, 4), nullable=False, server_default="0.0"),
        sa.Column("risk_score_30d", sa.Numeric(8, 4), nullable=False, server_default="0.0"),
        # Anomaly detection
        sa.Column("anomaly_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("anomaly_score", sa.Numeric(8, 4), nullable=True),
        # Audit metadata
        sa.Column("features_used", JSONB(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=False, server_default="'1.0.0'"),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["motor_id"], ["motors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_prediction_history_motor_id"),
        "prediction_history",
        ["motor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_history_predicted_at"),
        "prediction_history",
        ["predicted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_history_predicted_fault"),
        "prediction_history",
        ["predicted_fault"],
        unique=False,
    )
    op.create_index(
        "ix_prediction_history_motor_predicted_at",
        "prediction_history",
        ["motor_id", "predicted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_prediction_history_motor_predicted_at", table_name="prediction_history")
    op.drop_index(op.f("ix_prediction_history_predicted_fault"), table_name="prediction_history")
    op.drop_index(op.f("ix_prediction_history_predicted_at"), table_name="prediction_history")
    op.drop_index(op.f("ix_prediction_history_motor_id"), table_name="prediction_history")
    op.drop_table("prediction_history")
