"""add machine_id and fast_launch_machines ledger

Revision ID: 003
Revises: 002
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("provisioned_instances", sa.Column("machine_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_provisioned_instances_machine_id", "provisioned_instances", ["machine_id"])

    op.create_table(
        "fast_launch_machines",
        sa.Column("machine_id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("gpu_name", sa.String(), nullable=False),
        sa.Column("best_launch_seconds", sa.Integer(), nullable=False),
        sa.Column("fast_launch_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_vastai_instance_id", sa.BigInteger(), nullable=True),
        sa.Column("last_fast_launch_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_fast_launch_machines_gpu_name", "fast_launch_machines", ["gpu_name"])


def downgrade() -> None:
    op.drop_index("ix_fast_launch_machines_gpu_name", table_name="fast_launch_machines")
    op.drop_table("fast_launch_machines")
    op.drop_index("ix_provisioned_instances_machine_id", table_name="provisioned_instances")
    op.drop_column("provisioned_instances", "machine_id")
