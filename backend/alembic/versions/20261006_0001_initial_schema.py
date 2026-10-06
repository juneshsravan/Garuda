"""Initial GARUDA schema with 19 tables, RLS, citext and sequence

Revision ID: 20261006_0001
Revises: 
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261006_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ALL_TABLES = [
    "users",
    "sessions",
    "admin_users",
    "email_verification_codes",
    "scans",
    "messages",
    "images",
    "qr_codes",
    "urls",
    "analysis_results",
    "threat_indicators",
    "threats",
    "scan_threats",
    "threat_intelligence",
    "reports",
    "report_evidence",
    "report_status_history",
    "notifications",
    "audit_logs",
]


def upgrade() -> None:
    # 1. Enable citext extension
    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")

    # 2. Create Postgres sequence for report reference codes: GAR-{year}-{seq:06d}
    op.execute("CREATE SEQUENCE IF NOT EXISTS report_ref_seq START WITH 1 INCREMENT BY 1;")

    # 3. Create users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 4. Create sessions
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_refresh_token_hash", "sessions", ["refresh_token_hash"], unique=True)

    # 5. Create admin_users
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("admin_role", sa.String(length=50), nullable=False, server_default="analyst"),
        sa.Column("permissions", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_admin_users_user_id", "admin_users", ["user_id"], unique=True)

    # 6. Create email_verification_codes
    op.create_table(
        "email_verification_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_email_verification_codes_user_id", "email_verification_codes", ["user_id"])

    # 7. Create scans
    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scan_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="done"),
        sa.Column("input_sha256", sa.String(length=64), nullable=True),
        sa.Column("persisted_content", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_scans_user_id", "scans", ["user_id"])
    op.create_index("ix_scans_input_sha256", "scans", ["input_sha256"])
    op.create_index("ix_scans_user_id_created_at_desc", "scans", ["user_id", sa.text("created_at DESC")])

    # 8. Create messages
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("detected_language", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_messages_scan_id", "messages", ["scan_id"], unique=True)

    # 9. Create images
    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_images_scan_id", "images", ["scan_id"])
    op.create_index("ix_images_sha256", "images", ["sha256"])

    # 10. Create qr_codes
    op.create_table(
        "qr_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("images.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("payload_type", sa.String(length=50), nullable=False),
        sa.Column("upi_payee", sa.String(length=255), nullable=True),
        sa.Column("upi_name", sa.String(length=255), nullable=True),
        sa.Column("upi_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_qr_codes_scan_id", "qr_codes", ["scan_id"])
    op.create_index("ix_qr_codes_image_id", "qr_codes", ["image_id"])

    # 11. Create urls
    op.create_table(
        "urls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("registered_domain", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_urls_scan_id", "urls", ["scan_id"])
    op.create_index("ix_urls_registered_domain", "urls", ["registered_domain"])

    # 12. Create analysis_results
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("verification_status", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("legitimacy_signals", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("verify_steps", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("intel_status", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("engine_version", sa.String(length=50), nullable=False, server_default="2.0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_analysis_results_scan_id", "analysis_results", ["scan_id"], unique=True)
    op.create_index("ix_analysis_results_risk_level", "analysis_results", ["risk_level"])
    op.create_index("ix_analysis_results_category", "analysis_results", ["category"])

    # 13. Create threat_indicators
    op.create_table(
        "threat_indicators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_threat_indicators_analysis_id", "threat_indicators", ["analysis_id"])

    # 14. Create threats
    op.create_table(
        "threats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("threat_type", sa.String(length=50), nullable=False),
        sa.Column("value_hash", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_threats_value_hash", "threats", ["value_hash"], unique=True)

    # 15. Create scan_threats
    op.create_table(
        "scan_threats",
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("threat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("threats.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 16. Create threat_intelligence
    op.create_table(
        "threat_intelligence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("threat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("threats.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("indicator_type", sa.String(length=50), nullable=False),
        sa.Column("indicator_value", sa.Text(), nullable=False),
        sa.Column("indicator_hash", sa.String(length=64), nullable=False),
        sa.Column("verdict", sa.String(length=50), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_threat_intelligence_threat_id", "threat_intelligence", ["threat_id"])
    op.create_unique_constraint("uq_threat_intel_source_indicator_hash", "threat_intelligence", ["source", "indicator_hash"])
    op.create_index("ix_threat_intel_type_hash", "threat_intelligence", ["indicator_type", "indicator_hash"])

    # 17. Create reports
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_code", sa.String(length=32), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="submitted"),
        sa.Column("incident_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_reports_reference_code", "reports", ["reference_code"], unique=True)
    op.create_index("ix_reports_user_id", "reports", ["user_id"])
    op.create_index("ix_reports_scan_id", "reports", ["scan_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_user_id_created_at_desc", "reports", ["user_id", sa.text("created_at DESC")])

    # 18. Create report_evidence
    op.create_table(
        "report_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("text_value", sa.Text(), nullable=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_report_evidence_report_id", "report_evidence", ["report_id"])
    op.create_index("ix_report_evidence_scan_id", "report_evidence", ["scan_id"])

    # 19. Create report_status_history
    op.create_table(
        "report_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=True),
        sa.Column("to_status", sa.String(length=50), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_report_status_history_report_id", "report_status_history", ["report_id"])
    op.create_index("ix_report_status_history_changed_by", "report_status_history", ["changed_by"])

    # 20. Create notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id"],
        postgresql_where=sa.text("read_at IS NULL"),
    )

    # 21. Create audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index(
        "ix_audit_logs_created_at_brin",
        "audit_logs",
        ["created_at"],
        postgresql_using="brin",
    )

    # 22. Enable Row Level Security on ALL tables with NO policies (Source of Truth: ARCHITECTURE Section 2, 5)
    for table_name in ALL_TABLES:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    # Disable RLS and drop tables in reverse dependency order
    for table_name in reversed(ALL_TABLES):
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")

    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("report_status_history")
    op.drop_table("report_evidence")
    op.drop_table("reports")
    op.drop_table("threat_intelligence")
    op.drop_table("scan_threats")
    op.drop_table("threats")
    op.drop_table("threat_indicators")
    op.drop_table("analysis_results")
    op.drop_table("urls")
    op.drop_table("qr_codes")
    op.drop_table("images")
    op.drop_table("messages")
    op.drop_table("scans")
    op.drop_table("email_verification_codes")
    op.drop_table("admin_users")
    op.drop_table("sessions")
    op.drop_table("users")

    op.execute("DROP SEQUENCE IF EXISTS report_ref_seq;")
    # Extension citext is retained or dropped
