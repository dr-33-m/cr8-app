"""create provisioning tables

Revision ID: 002
Revises: 001
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provisioned_instances",
        sa.Column("vastai_instance_id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("lifecycle_state", sa.String(), nullable=False),
        sa.Column("gpu_name", sa.String(), nullable=False),
        sa.Column("host", sa.String(), nullable=True),
        sa.Column("ssh_port", sa.Integer(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=False),
        sa.Column("vastai_actual_status", sa.String(), nullable=True),
        sa.Column("vastai_cur_state", sa.String(), nullable=True),
        sa.Column("vastai_intended_status", sa.String(), nullable=True),
        sa.Column("vastai_next_state", sa.String(), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_state_change_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("phase_detail", sa.String(), nullable=True),
        sa.Column("last_error_reason", sa.String(), nullable=True),
        sa.Column("last_error_message", sa.String(), nullable=True),
        sa.Column("adopted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("destroyed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "instance_user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "vastai_instance_id",
            sa.BigInteger(),
            sa.ForeignKey("provisioned_instances.vastai_instance_id"),
            nullable=False,
        ),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("blender_pid", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_instance_user_sessions_username", "instance_user_sessions", ["username"])
    op.create_index(
        "ux_one_active_session_per_user",
        "instance_user_sessions",
        ["username"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )

    op.create_table(
        "teardown_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vastai_instance_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_teardown_intents_vastai_instance_id", "teardown_intents", ["vastai_instance_id"])
    op.create_index(
        "ux_open_teardown_per_instance",
        "teardown_intents",
        ["vastai_instance_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('confirmed_destroyed', 'confirmed_absent')"),
    )

    op.create_table(
        "provisioning_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vastai_instance_id", sa.BigInteger(), nullable=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("detail", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_provisioning_events_vastai_instance_id", "provisioning_events", ["vastai_instance_id"])
    op.create_index("ix_provisioning_events_username", "provisioning_events", ["username"])


def downgrade() -> None:
    op.drop_table("provisioning_events")
    op.drop_index("ux_open_teardown_per_instance", table_name="teardown_intents")
    op.drop_index("ix_teardown_intents_vastai_instance_id", table_name="teardown_intents")
    op.drop_table("teardown_intents")
    op.drop_index("ux_one_active_session_per_user", table_name="instance_user_sessions")
    op.drop_index("ix_instance_user_sessions_username", table_name="instance_user_sessions")
    op.drop_table("instance_user_sessions")
    op.drop_table("provisioned_instances")
