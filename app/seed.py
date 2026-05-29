from pathlib import Path

from sqlmodel import Session, select

from app.db import create_db_and_tables, engine
from app.models import Topic

QUESTIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "questions"

INITIAL_TOPICS = [
    {
        "name": "Mạng máy tính và Internet",
        "order_in_syllabus": 1,
        "description": "Bài 1 SGK Tin 10 Cánh Diều — khái niệm mạng, Internet, giao thức, dịch vụ.",
    },
    {
        "name": "Dữ liệu, thông tin và xử lý thông tin",
        "order_in_syllabus": 2,
        "description": "Bài 6 SGK — biểu diễn dữ liệu, thông tin số, xử lý thông tin.",
    },
    {
        "name": "Python cơ bản",
        "order_in_syllabus": 3,
        "description": "Bài 16 SGK — ngôn ngữ lập trình bậc cao, cú pháp Python, biến, kiểu dữ liệu.",
    },
    {
        "name": "Lập trình giải bài toán",
        "order_in_syllabus": 4,
        "description": "Bài 18 SGK — phân tích bài toán, thuật toán, cấu trúc rẽ nhánh và lặp.",
    },
]


def seed_topics(session: Session) -> int:
    existing = session.exec(select(Topic)).first()
    if existing is not None:
        return 0

    for item in INITIAL_TOPICS:
        session.add(Topic(**item))
    session.commit()
    return len(INITIAL_TOPICS)


def seed_questions(session: Session) -> int:
    """Import questions from data/questions/topic-*.json if Question table is empty.

    Returns number of questions inserted.
    """
    from scripts.import_questions import import_questions, load_and_validate

    files = sorted(QUESTIONS_DIR.glob("topic-*.json"))
    if not files:
        return 0
    questions = load_and_validate(files)
    inserted, _ = import_questions(questions, session)
    return inserted


def init_db() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        t = seed_topics(session)
        if t:
            print(f"[seed] inserted {t} topics")
        q = seed_questions(session)
        if q:
            print(f"[seed] inserted {q} questions")


if __name__ == "__main__":
    init_db()
    print("[seed] DB ready at", engine.url)
