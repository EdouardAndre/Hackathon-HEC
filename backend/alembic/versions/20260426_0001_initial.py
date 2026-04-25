"""Initial schema

Revision ID: 20260426_0001
Revises:
Create Date: 2026-04-26 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260426_0001"
down_revision = None
branch_labels = None
depends_on = None


purchaseorderstatus = sa.Enum("draft", "confirmed", name="purchaseorderstatus")


def upgrade() -> None:
    purchaseorderstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "inventory_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_level", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("available_quantity", sa.Integer(), nullable=False),
        sa.Column("current_unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", purchaseorderstatus, nullable=False),
        sa.Column("expected_shortage_date", sa.Date(), nullable=False),
        sa.Column("ap2_reference", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("purchase_orders")
    op.drop_table("suppliers")
    op.drop_table("inventory_snapshots")
    purchaseorderstatus.drop(op.get_bind(), checkfirst=True)
