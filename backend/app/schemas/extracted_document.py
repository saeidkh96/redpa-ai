from pydantic import BaseModel, Field


class ExtractedDocument(BaseModel):
    text: str = Field(..., description="Extracted plain text")
    page_count: int = Field(default=1)
    metadata: dict[str, str] = Field(default_factory=dict)