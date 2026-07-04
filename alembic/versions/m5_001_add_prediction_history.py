"""add prediction_history table

Revision ID: m5_001
Revises: m4_001
Create Date: 2024-01-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "m5_001"
down_revision = "m4_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prediction_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "motor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("motors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Fault classification
        sa.Column("predicted_fault", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        # Health
        sa.Column("health_score", sa.Float(), nullable=False),
        sa.Column("health_status", sa.String(20), nullable=False),
        # Risk
        sa.Column("risk_score_7d", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_score_30d", sa.Float(), nullable=False, server_default="0.0"),
        # Anomaly
        sa.Column("anomaly_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("anomaly_score", sa.Float(), nullable=True),
        # Metadata
        sa.Column("features_used", JSONB(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        # Timestamps
        sa.Column(
            "prediction_date",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_prediction_history_motor_id",
        "prediction_history",
        ["motor_id"],
    )
    op.create_index(
        "ix_prediction_history_prediction_date",
        "prediction_history",
        ["prediction_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_prediction_history_prediction_date", table_name="prediction_history")
    op.drop_index("ix_prediction_history_motor_id", table_name="prediction_history")
    op.drop_table("prediction_history")
