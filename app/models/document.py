from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB


class LangchainPgVector(SQLModel, table=True):

    __tablename__ = "langchain_pg_vector"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_column_kwargs={"type": PG_UUID(as_uuid=True)},
    )

    embedding: list[float] = Field(sa_column_kwargs={"type": "vector(768)"})

    content: str = Field(index=True)

    metadata: Optional[dict] = Field(default={}, sa_column_kwargs={"type": JSONB})

    created_at: datetime = Field(default_factory=datetime.utcnow)
