from extensions import db
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Aggiungi la colonna corso_id
    op.add_column('disponibilita_docente', 
        sa.Column('corso_id', sa.Integer(), sa.ForeignKey('corso.id'), nullable=True)
    )

def downgrade():
    # Rimuovi la colonna corso_id
    op.drop_column('disponibilita_docente', 'corso_id') 