import json
from pathlib import Path

import pytest
from sqlmodel import Session, select

from app.models import Question, Topic
from scripts.import_questions import (
    QUESTIONS_DIR,
    ValidationError,
    import_questions,
    load_and_validate,
    validate_question,
)


# ---- validate_question unit tests ----

def _good_q():
    return {
        "topic_id": 1,
        "content": "Câu mẫu?",
        "difficulty_level": 1,
        "options": ["A", "B", "C", "D"],
        "correct_answer": "B",
    }


def test_validate_good():
    validate_question(_good_q(), "test.json", 0)


def test_validate_missing_field():
    q = _good_q()
    del q["correct_answer"]
    with pytest.raises(ValidationError, match="missing fields"):
        validate_question(q, "test.json", 0)


def test_validate_empty_content():
    q = _good_q()
    q["content"] = "   "
    with pytest.raises(ValidationError, match="content"):
        validate_question(q, "test.json", 0)


def test_validate_bad_difficulty():
    q = _good_q()
    q["difficulty_level"] = 5
    with pytest.raises(ValidationError, match="difficulty_level"):
        validate_question(q, "test.json", 0)


def test_validate_options_not_list():
    q = _good_q()
    q["options"] = "ABCD"
    with pytest.raises(ValidationError, match="options"):
        validate_question(q, "test.json", 0)


def test_validate_options_wrong_count():
    q = _good_q()
    q["options"] = ["A", "B", "C"]
    with pytest.raises(ValidationError, match="options"):
        validate_question(q, "test.json", 0)


def test_validate_options_duplicate():
    q = _good_q()
    q["options"] = ["A", "B", "A", "D"]
    with pytest.raises(ValidationError, match="unique"):
        validate_question(q, "test.json", 0)


def test_validate_correct_not_in_options():
    q = _good_q()
    q["correct_answer"] = "Z"
    with pytest.raises(ValidationError, match="not in options"):
        validate_question(q, "test.json", 0)


# ---- load_and_validate integration ----

def test_load_and_validate_real_files():
    files = sorted(QUESTIONS_DIR.glob("topic-*.json"))
    assert len(files) == 4, f"expected 4 topic files, got {len(files)}"
    questions = load_and_validate(files)
    assert len(questions) == 120, f"expected 120 questions, got {len(questions)}"


def test_distribution_per_topic_per_level():
    files = sorted(QUESTIONS_DIR.glob("topic-*.json"))
    questions = load_and_validate(files)
    counts: dict[tuple[int, int], int] = {}
    for q in questions:
        key = (q["topic_id"], q["difficulty_level"])
        counts[key] = counts.get(key, 0) + 1
    for topic_id in (1, 2, 3, 4):
        for level in (1, 2, 3):
            assert counts.get((topic_id, level)) == 10, (
                f"topic {topic_id} level {level}: expected 10, got {counts.get((topic_id, level))}"
            )


def test_load_invalid_json(tmp_path: Path):
    bad = tmp_path / "topic-99.json"
    bad.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(ValidationError, match="invalid JSON"):
        load_and_validate([bad])


def test_load_root_not_array(tmp_path: Path):
    bad = tmp_path / "topic-99.json"
    bad.write_text('{"not": "array"}', encoding="utf-8")
    with pytest.raises(ValidationError, match="must be JSON array"):
        load_and_validate([bad])


# ---- import_questions DB integration ----

@pytest.fixture()
def seeded_topics(session: Session):
    for i in range(1, 5):
        session.add(Topic(id=i, name=f"T{i}", order_in_syllabus=i))
    session.commit()


def test_import_questions_into_db(session: Session, seeded_topics):
    questions = load_and_validate(sorted(QUESTIONS_DIR.glob("topic-*.json")))
    inserted, skipped = import_questions(questions, session)
    assert inserted == 120
    assert skipped == 0
    db_count = len(session.exec(select(Question)).all())
    assert db_count == 120


def test_import_idempotent(session: Session, seeded_topics):
    questions = load_and_validate(sorted(QUESTIONS_DIR.glob("topic-*.json")))
    import_questions(questions, session)
    inserted2, skipped2 = import_questions(questions, session)
    assert inserted2 == 0
    assert skipped2 == 120
    db_count = len(session.exec(select(Question)).all())
    assert db_count == 120


def test_import_rejects_invalid_topic_id(session: Session, seeded_topics):
    bad = [{
        "topic_id": 999,
        "content": "x",
        "difficulty_level": 1,
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
    }]
    with pytest.raises(ValidationError, match="topic_id 999"):
        import_questions(bad, session)


def test_options_stored_as_json(session: Session, seeded_topics):
    questions = load_and_validate(sorted(QUESTIONS_DIR.glob("topic-*.json")))
    import_questions(questions, session)
    q = session.exec(select(Question)).first()
    parsed = json.loads(q.options_json)
    assert isinstance(parsed, list)
    assert len(parsed) == 4
    assert q.correct_answer in parsed
