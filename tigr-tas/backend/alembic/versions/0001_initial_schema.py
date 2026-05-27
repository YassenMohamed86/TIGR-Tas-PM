"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2023-10-18 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # 2. Create ENUM types
    job_status_enum = postgresql.ENUM('PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='job_status')
    job_status_enum.create(op.get_bind())

    upload_status_enum = postgresql.ENUM('UPLOADING', 'COMPLETE', 'FAILED', 'QUARANTINED', name='upload_status')
    upload_status_enum.create(op.get_bind())

    # 3. Create analysis_jobs table
    op.create_table('analysis_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM(name='job_status', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('priority BETWEEN 1 AND 10', name='check_priority_range'),
        sa.CheckConstraint('progress BETWEEN 0 AND 100', name='check_progress_range')
    )
    op.create_index(op.f('ix_analysis_jobs_celery_task_id'), 'analysis_jobs', ['celery_task_id'], unique=False)
    op.create_index(op.f('ix_analysis_jobs_job_type'), 'analysis_jobs', ['job_type'], unique=False)
    op.create_index('ix_analysis_jobs_org_status', 'analysis_jobs', ['org_id', 'status'], unique=False)
    op.create_index('ix_analysis_jobs_status_created_at', 'analysis_jobs', ['status', 'created_at'], unique=False)

    # 4. Create genome_files table
    op.create_table('genome_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('original_name', sa.String(length=255), nullable=False),
        sa.Column('stored_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('file_extension', sa.String(length=20), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('md5_hash', sa.String(length=32), nullable=True),
        sa.Column('sha256_hash', sa.String(length=64), nullable=True),
        sa.Column('upload_status', postgresql.ENUM(name='upload_status', create_type=False), nullable=False, server_default='UPLOADING'),
        sa.Column('genome_build', sa.String(length=20), nullable=True),
        sa.Column('annotation', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_genome_files_file_extension'), 'genome_files', ['file_extension'], unique=False)
    op.create_index(op.f('ix_genome_files_md5_hash'), 'genome_files', ['md5_hash'], unique=False)
    op.create_index('ix_genome_files_org_status', 'genome_files', ['org_id', 'upload_status'], unique=False)

def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_genome_files_org_status', table_name='genome_files')
    op.drop_index(op.f('ix_genome_files_md5_hash'), table_name='genome_files')
    op.drop_index(op.f('ix_genome_files_file_extension'), table_name='genome_files')
    
    op.drop_index('ix_analysis_jobs_status_created_at', table_name='analysis_jobs')
    op.drop_index('ix_analysis_jobs_org_status', table_name='analysis_jobs')
    op.drop_index(op.f('ix_analysis_jobs_job_type'), table_name='analysis_jobs')
    op.drop_index(op.f('ix_analysis_jobs_celery_task_id'), table_name='analysis_jobs')
    
    # Drop tables
    op.drop_table('genome_files')
    op.drop_table('analysis_jobs')
    
    # Drop ENUMs
    postgresql.ENUM(name='upload_status').drop(op.get_bind())
    postgresql.ENUM(name='job_status').drop(op.get_bind())
    
    # Drop extension (optional, usually left alone as other DBs might use it, but spec says to drop it)
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
