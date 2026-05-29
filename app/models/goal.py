from datetime import datetime
from sqlmodel import Field, SQLModel

GOAL_TYPES = ("exam", "new_topic", "improve", "challenge")


class LearningGoal(SQLModel, table=True):
    __tablename__ = "learning_goal"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    goal_type: str
    set_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, index=True)
