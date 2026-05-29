import json

from sqlmodel import Session, select

from app.models import Topic
from app.seed import INITIAL_TOPICS, seed_topics


def test_seed_topics_inserts_initial(session: Session):
    n = seed_topics(session)
    assert n == len(INITIAL_TOPICS)
    rows = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    assert [r.name for r in rows] == [t["name"] for t in INITIAL_TOPICS]
    assert [r.order_in_syllabus for r in rows] == [1, 2, 3, 4]


def test_seed_topics_idempotent(session: Session):
    first = seed_topics(session)
    second = seed_topics(session)
    assert first == len(INITIAL_TOPICS)
    assert second == 0
    count = len(session.exec(select(Topic)).all())
    assert count == len(INITIAL_TOPICS)


def test_initial_topics_have_required_fields():
    for item in INITIAL_TOPICS:
        assert "name" in item and item["name"]
        assert "order_in_syllabus" in item
        assert isinstance(item["order_in_syllabus"], int)
