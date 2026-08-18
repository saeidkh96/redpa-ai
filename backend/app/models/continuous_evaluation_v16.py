from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, JSON, String, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base
class AgentEvaluationRecord(Base):
    __tablename__="agent_evaluation_records"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    user_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False,index=True)
    subject:Mapped[str]=mapped_column(String(180),nullable=False,index=True)
    status:Mapped[str]=mapped_column(String(40),nullable=False)
    score:Mapped[float]=mapped_column(Float,nullable=False,default=0.0)
    allowed:Mapped[bool]=mapped_column(Boolean,nullable=False,default=False)
    payload:Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,default=lambda:datetime.now(timezone.utc))
