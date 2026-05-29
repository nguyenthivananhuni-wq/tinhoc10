from sqlmodel import Field, SQLModel


class Topic(SQLModel, table=True):
    __tablename__ = "topic"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    order_in_syllabus: int
    parent_id: int | None = Field(default=None, foreign_key="topic.id")
    description: str | None = None
