"""0001 Initial Schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-10 22:11:00.000000

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sql_path = Path(__file__).with_name("0001_initial_schema.sql")
    if sql_path.exists():
        sql_content = sql_path.read_text(encoding="utf-8")
        op.execute(sa.text(sql_content))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS deterministic_risk_assessments CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS analyzer_execution_records CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS canonical_evidence CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS investigations CASCADE;"))
