from datetime import datetime
from sqlmodel import Field, SQLModel


class Question(SQLModel, table=True):
    __tablename__ = "question"

    id: int | None = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    content: str
    difficulty_level: int = Field(ge=1, le=3, index=True)
    type: str = Field(default="mcq")
    difficulty_b: float = Field(default=0.0)
    options_json: str
    correct_answer: str
    source_page: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
