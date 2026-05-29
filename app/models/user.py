from datetime import datetime
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=30)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ability_theta: float = Field(default=0.0)
    is_admin: bool = Field(default=False)
