"""create core persistence tables

Revision ID: 0001_create_core_tables
Revises:
Create Date: 2026-06-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_create_core_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "motors",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("manufacturer", sa.String(length=120), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("rated_power_kw", sa.Numeric(10, 2), nullable=False),
        sa.Column("rated_voltage", sa.Numeric(10, 2), nullable=False),
        sa.Column("rated_current", sa.Numeric(10, 2), nullable=False),
        sa.Column("rpm", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_motors_location"), "motors", ["location"], unique=False)
    op.create_index(op.f("ix_motors_name"), "motors", ["name"], unique=False)
    op.create_index(op.f("ix_motors_status"), "motors", ["status"], unique=False)

    op.create_table(
        "fault_history",
        sa.Column("motor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("fault_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["motor_id"], ["motors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fault_history_detected_at"), "fault_history", ["detected_at"], unique=False)
    op.create_index(op.f("ix_fault_history_fault_type"), "fault_history", ["fault_type"], unique=False)
    op.create_index(op.f("ix_fault_history_motor_id"), "fault_history", ["motor_id"], unique=False)
    op.create_index(op.f("ix_fault_history_severity"), "fault_history", ["severity"], unique=False)

    op.create_table(
        "maintenance_history",
        sa.Column("motor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("maintenance_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("performed_by", sa.String(length=120), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["motor_id"], ["motors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_maintenance_history_maintenance_type"), "maintenance_history", ["maintenance_type"], unique=False)
    op.create_index(op.f("ix_maintenance_history_motor_id"), "maintenance_history", ["motor_id"], unique=False)
    op.create_index(op.f("ix_maintenance_history_next_due_at"), "maintenance_history", ["next_due_at"], unique=False)
    op.create_index(op.f("ix_maintenance_history_performed_at"), "maintenance_history", ["performed_at"], unique=False)

    op.create_table(
        "recommendations",
        sa.Column("motor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("recommended_actions", sa.Text(), nullable=False),
        sa.Column("maintenance_plan", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["motor_id"], ["motors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendations_created_at"), "recommendations", ["created_at"], unique=False)
    op.create_index(op.f("ix_recommendations_motor_id"), "recommendations", ["motor_id"], unique=False)
    op.create_index(op.f("ix_recommendations_risk_level"), "recommendations", ["risk_level"], unique=False)

    op.create_table(
        "sensor_data",
        sa.Column("motor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("temperature", sa.Numeric(10, 3), nullable=False),
        sa.Column("vibration", sa.Numeric(10, 3), nullable=False),
        sa.Column("current", sa.Numeric(10, 3), nullable=False),
        sa.Column("voltage", sa.Numeric(10, 3), nullable=False),
        sa.Column("power", sa.Numeric(10, 3), nullable=False),
        sa.Column("power_factor", sa.Numeric(5, 3), nullable=False),
        sa.Column("thd", sa.Numeric(6, 3), nullable=False),
        sa.Column("load", sa.Numeric(6, 3), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["motor_id"], ["motors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sensor_data_motor_id"), "sensor_data", ["motor_id"], unique=False)
    op.create_index("ix_sensor_data_motor_timestamp", "sensor_data", ["motor_id", "timestamp"], unique=False)
    op.create_index(op.f("ix_sensor_data_timestamp"), "sensor_data", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sensor_data_timestamp"), table_name="sensor_data")
    op.drop_index("ix_sensor_data_motor_timestamp", table_name="sensor_data")
    op.drop_index(op.f("ix_sensor_data_motor_id"), table_name="sensor_data")
    op.drop_table("sensor_data")

    op.drop_index(op.f("ix_recommendations_risk_level"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_motor_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_created_at"), table_name="recommendations")
    op.drop_table("recommendations")

    op.drop_index(op.f("ix_maintenance_history_performed_at"), table_name="maintenance_history")
    op.drop_index(op.f("ix_maintenance_history_next_due_at"), table_name="maintenance_history")
    op.drop_index(op.f("ix_maintenance_history_motor_id"), table_name="maintenance_history")
    op.drop_index(op.f("ix_maintenance_history_maintenance_type"), table_name="maintenance_history")
    op.drop_table("maintenance_history")

    op.drop_index(op.f("ix_fault_history_severity"), table_name="fault_history")
    op.drop_index(op.f("ix_fault_history_motor_id"), table_name="fault_history")
    op.drop_index(op.f("ix_fault_history_fault_type"), table_name="fault_history")
    op.drop_index(op.f("ix_fault_history_detected_at"), table_name="fault_history")
    op.drop_table("fault_history")

    op.drop_index(op.f("ix_motors_status"), table_name="motors")
    op.drop_index(op.f("ix_motors_name"), table_name="motors")
    op.drop_index(op.f("ix_motors_location"), table_name="motors")
    op.drop_table("motors")
