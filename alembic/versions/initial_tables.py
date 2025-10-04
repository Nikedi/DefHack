"""Initial tables

Revision ID: initial_tables
Revises: 
Create Date: 2025-10-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sensor_reading table
    op.execute("""
        CREATE TABLE sensor_reading (
          time                TIMESTAMPTZ NOT NULL,
          sensor_id           TEXT NOT NULL,
          unit                TEXT,
          observer_signature  TEXT NOT NULL,
          mgrs                TEXT NOT NULL CHECK (mgrs ~ '^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$'),
          what                TEXT NOT NULL,
          amount              NUMERIC,
          confidence          INT NOT NULL CHECK (confidence BETWEEN 0 AND 100),
          received_at         TIMESTAMPTZ DEFAULT now()
        );
    """)
    
    # Create report table
    op.execute("""
        CREATE TABLE report (
          id                  SERIAL PRIMARY KEY,
          source              TEXT CHECK (source IN ('sensor','telegram','analyst')) NOT NULL,
          unit                TEXT,
          observer_signature  TEXT NOT NULL,
          occurred_at         TIMESTAMPTZ NOT NULL,
          title               TEXT,
          body                TEXT,
          confidence          INT CHECK (confidence BETWEEN 0 AND 100),
          mgrs                TEXT NOT NULL CHECK (mgrs ~ '^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$'),
          attachments         JSONB NOT NULL DEFAULT '[]'
        );
    """)
    
    # Create intel_doc table
    op.execute("""
        CREATE TABLE intel_doc (
          id SERIAL PRIMARY KEY,
          title TEXT NOT NULL,
          version TEXT,
          object_key TEXT NOT NULL,
          checksum TEXT NOT NULL,
          source_type TEXT NOT NULL DEFAULT 'pdf',
          lang TEXT,
          published_at DATE,
          origin TEXT,
          adversary TEXT,
          created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    
    # Create doc_chunk table (without vector type for now)
    op.execute("""
        CREATE TABLE doc_chunk (
          id SERIAL PRIMARY KEY,
          doc_id INT NOT NULL REFERENCES intel_doc(id) ON DELETE CASCADE,
          chunk_idx INT NOT NULL,
          text TEXT NOT NULL,
          tokens INT,
          page INT,
          para INT,
          line_start INT,
          line_end INT,
          step_id TEXT,
          section TEXT,
          embedding TEXT,
          tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
        );
    """)
    
    # Create basic indexes
    op.execute("CREATE INDEX idx_doc_chunk_tsv ON doc_chunk USING GIN (tsv);")
    # Skip trigram indexes for now as pg_trgm extension may not be available
    # op.execute("CREATE INDEX idx_report_mgrs_trgm ON report USING GIN (mgrs gin_trgm_ops);")
    # op.execute("CREATE INDEX idx_sensor_mgrs_trgm ON sensor_reading USING GIN (mgrs gin_trgm_ops);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS doc_chunk CASCADE;")
    op.execute("DROP TABLE IF EXISTS intel_doc CASCADE;")
    op.execute("DROP TABLE IF EXISTS report CASCADE;")
    op.execute("DROP TABLE IF EXISTS sensor_reading CASCADE;")