"""0002 Phase 2 Canonical Investigation System

Revision ID: 0002_phase2
Revises: 0001_initial_schema
Create Date: 2026-10-10 22:15:00.000000

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_phase2"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sql_path = Path(__file__).with_name("0002_phase2_canonical_investigation_system.sql")
    if sql_path.exists():
        sql_content = sql_path.read_text(encoding="utf-8")
        op.execute(sa.text(sql_content))


def downgrade() -> None:
    tables = [
        "audit_events",
        "report_manifests",
        "analyzer_execution_records",
        "artifacts",
        "graph_edges",
        "entities",
        "verification_results",
        "risk_signals",
        "evidence",
        "inputs",
        "investigations",
        "users",
    ]
    for table in tables:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
