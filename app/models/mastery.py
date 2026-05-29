from datetime import datetime
from sqlmodel import Field, SQLModel


class MasteryState(SQLModel, table=True):
    __tablename__ = "mastery_state"

    user_id: int = Field(foreign_key="user.id", primary_key=True)
    topic_id: int = Field(foreign_key="topic.id", primary_key=True)
    p_mastery: float = Field(default=0.1)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
