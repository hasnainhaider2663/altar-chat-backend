from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy import Column, DateTime, func
from datetime import datetime


class LangchainPgVector(SQLModel, table=True):
    __tablename__ = "langchain_pg_vector"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4),
    )

    embedding: list[float] = Field(sa_column=Column("vector(768)"))

    content: str = Field()

    doc_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSONB),  # maps to DB column `metadata`
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
