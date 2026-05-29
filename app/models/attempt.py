from datetime import datetime
from sqlmodel import Field, SQLModel


class Attempt(SQLModel, table=True):
    __tablename__ = "attempt"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    is_correct: bool
    response_time_ms: int = Field(default=0)
    selected_answer: str | None = None
    attempted_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    session_id: str | None = Field(default=None, index=True)
