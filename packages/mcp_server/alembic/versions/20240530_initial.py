"""Initial database migration

Revision ID: 20240530_initial
Revises: 
Create Date: 2024-05-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240530_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create task status and type enums
    op.execute("CREATE TYPE taskstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE tasktype AS ENUM ('crawl', 'research', 'document')")
    
    # Create tasks table
    op.create_table(
        'task',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('type', sa.Enum('crawl', 'research', 'document', name='tasktype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='taskstatus'), nullable=False),
        sa.Column('parameters', sa.JSON, nullable=False),
        sa.Column('progress', sa.Integer, nullable=False),
        sa.Column('error', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Create task results table
    op.create_table(
        'taskresult',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('task.id'), nullable=False),
        sa.Column('result_type', sa.String(50), nullable=False),
        sa.Column('data', sa.JSON, nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Create webpage table
    op.create_table(
        'webpage',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('domain', sa.String(256), nullable=False),
        sa.Column('title', sa.String(512), nullable=True),
        sa.Column('content', sa.JSON, nullable=False),
        sa.Column('html', sa.Text, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('doc_type', sa.String(50), nullable=True),
        sa.Column('processed', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Create indexes
    op.create_index('ix_webpage_domain', 'webpage', ['domain'])
    op.create_index('ix_webpage_url', 'webpage', ['url'], unique=True)
    
    # Create page links table
    op.create_table(
        'page_links',
        sa.Column('source_id', sa.String(36), sa.ForeignKey('webpage.id'), primary_key=True),
        sa.Column('target_id', sa.String(36), sa.ForeignKey('webpage.id'), primary_key=True)
    )
    
    # Create assets table
    op.create_table(
        'asset',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('webpage_id', sa.String(36), sa.ForeignKey('webpage.id'), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('size', sa.Integer, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Create documentation structure table
    op.create_table(
        'documentationstructure',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('webpage_id', sa.String(36), sa.ForeignKey('webpage.id'), nullable=False),
        sa.Column('structure_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(512), nullable=True),
        sa.Column('content', sa.JSON, nullable=False),
        sa.Column('parent_id', sa.String(36), sa.ForeignKey('documentationstructure.id'), nullable=True),
        sa.Column('order', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

def downgrade() -> None:
    # Drop tables
    op.drop_table('documentationstructure')
    op.drop_table('asset')
    op.drop_table('page_links')
    op.drop_table('webpage')
    op.drop_table('taskresult')
    op.drop_table('task')
    
    # Drop enums
    op.execute("DROP TYPE taskstatus")
    op.execute("DROP TYPE tasktype")

