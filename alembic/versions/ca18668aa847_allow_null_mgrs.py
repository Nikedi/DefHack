"""allow_null_mgrs

Revision ID: ca18668aa847
Revises: e0af44e5b1c3
Create Date: 2025-10-05 00:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca18668aa847'
down_revision: Union[str, None] = 'e0af44e5b1c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Allow NULL values for mgrs in sensor_reading table
    op.execute("""
        ALTER TABLE sensor_reading 
        ALTER COLUMN mgrs DROP NOT NULL,
        ALTER COLUMN mgrs DROP CONSTRAINT sensor_reading_mgrs_check;
    """)
    
    # Add new check constraint that allows NULL or valid MGRS format
    op.execute("""
        ALTER TABLE sensor_reading
        ADD CONSTRAINT sensor_reading_mgrs_check 
        CHECK (mgrs IS NULL OR mgrs ~ '^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$');
    """)
    
    # Allow NULL values for mgrs in report table
    op.execute("""
        ALTER TABLE report 
        ALTER COLUMN mgrs DROP NOT NULL,
        ALTER COLUMN mgrs DROP CONSTRAINT report_mgrs_check;
    """)
    
    # Add new check constraint that allows NULL or valid MGRS format
    op.execute("""
        ALTER TABLE report
        ADD CONSTRAINT report_mgrs_check 
        CHECK (mgrs IS NULL OR mgrs ~ '^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$');
    """)


def downgrade() -> None:
    # Revert report table mgrs column to NOT NULL
    op.execute("""
        UPDATE report SET mgrs = '01CAA0000000000' WHERE mgrs IS NULL;
    """)
    op.execute("""
        ALTER TABLE report 
        DROP CONSTRAINT report_mgrs_check,
        ALTER COLUMN mgrs SET NOT NULL;
    """)
    op.execute("""
        ALTER TABLE report
        ADD CONSTRAINT report_mgrs_check 
        CHECK (mgrs ~ '^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$');
    """)
    
    # Revert sensor_reading table mgrs column to NOT NULL
    op.execute("""
        UPDATE sensor_reading SET mgrs = '01CAA0000000000' WHERE mgrs IS NULL;
    """)
    op.execute("""
        ALTER TABLE sensor_reading 
        DROP CONSTRAINT sensor_reading_mgrs_check,
        ALTER COLUMN mgrs SET NOT NULL;
    """)
    op.execute("""
        ALTER TABLE sensor_reading
        ADD CONSTRAINT sensor_reading_mgrs_check 
        CHECK (mgrs ~ '^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$');
    """)