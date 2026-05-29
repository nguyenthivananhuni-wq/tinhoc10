"""Recommendation engine — combines BKT mastery, learning goal, and IRT ability.

Two responsibilities:

1. `recommend_topics(...)` — rule-based topic ranking by goal (BRAINSTORM §5.4):
       exam      → ưu tiên topic mastery thấp nhất (củng cố trước thi).
       improve   → topic mastery < 0.5.
       new_topic → topic kế tiếp trong syllabus mà prerequisite mastery ≥ 0.7.
       challenge → topic mastery ≥ 0.8 (sẵn sàng làm câu khó).

2. `select_question(...)` — IRT adaptive item selection: trong topic đã chọn,
   pick câu có |difficulty_b − theta| nhỏ nhất (Rasch: Fisher info cực đại ở b≈θ),
   loại các câu vừa làm gần đây.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models import Attempt, Question, Topic

# Mastery mặc định cho topic chưa có MasteryState row (= BKT P(L0)).
DEFAULT_MASTERY = 0.1

# Ngưỡng rule (BRAINSTORM §5.4).
PREREQ_THRESHOLD = 0.7   # new_topic: prerequisite mastery cần đạt
IMPROVE_THRESHOLD = 0.5  # improve: topic dưới ngưỡng này
CHALLENGE_THRESHOLD = 0.8  # challenge: topic trên ngưỡng này

# Mặc định loại câu đã làm trong khoảng thời gian này (tránh lặp câu).
RECENT_WINDOW = timedelta(hours=24)


def _mastery_of(topic_id: int, mastery_map: dict[int, float]) -> float:
    return mastery_map.get(topic_id, DEFAULT_MASTERY)


def recommend_topics(
    topics: list[Topic],
    mastery_map: dict[int, float],
    goal_type: str,
    n: int = 3,
) -> list[dict]:
    """Rank topics theo goal, trả tối đa `n` gợi ý kèm explain text.

    Mỗi item: {topic, p_mastery, percent, reason}. Luôn trả ≥1 item nếu có topic
    (fallback khi không topic nào thỏa rule cứng).
    """
    if not topics:
        return []

    ordered = sorted(topics, key=lambda t: t.order_in_syllabus)
    ranked: list[tuple[Topic, str]] = []

    if goal_type == "improve":
        weak = [t for t in ordered if _mastery_of(t.id, mastery_map) < IMPROVE_THRESHOLD]
        weak.sort(key=lambda t: _mastery_of(t.id, mastery_map))
        for t in weak:
            pct = round(_mastery_of(t.id, mastery_map) * 100)
            ranked.append((t, f"Mastery '{t.name}' mới {pct}% (<50%) — nên luyện thêm để cải thiện."))
        if not ranked:  # tất cả đã ≥ 0.5 → vẫn gợi ý topic yếu nhất
            t = min(ordered, key=lambda t: _mastery_of(t.id, mastery_map))
            pct = round(_mastery_of(t.id, mastery_map) * 100)
            ranked.append((t, f"Bạn đã khá đều; '{t.name}' ({pct}%) là chủ đề thấp nhất, củng cố thêm."))

    elif goal_type == "challenge":
        strong = [t for t in ordered if _mastery_of(t.id, mastery_map) >= CHALLENGE_THRESHOLD]
        strong.sort(key=lambda t: _mastery_of(t.id, mastery_map), reverse=True)
        for t in strong:
            pct = round(_mastery_of(t.id, mastery_map) * 100)
            ranked.append((t, f"Bạn đã giỏi '{t.name}' ({pct}% ≥ 80%) — thử các câu khó để vượt giới hạn."))
        if not ranked:  # chưa topic nào ≥ 0.8 → gợi ý topic mạnh nhất
            t = max(ordered, key=lambda t: _mastery_of(t.id, mastery_map))
            pct = round(_mastery_of(t.id, mastery_map) * 100)
            ranked.append((t, f"Chưa chủ đề nào đạt 80%; '{t.name}' ({pct}%) là mạnh nhất — luyện để sẵn sàng thách thức."))

    elif goal_type == "new_topic":
        # Topic kế tiếp trong syllabus mà prerequisite (topic ngay trước) đã ≥ 0.7.
        for i, t in enumerate(ordered):
            m = _mastery_of(t.id, mastery_map)
            if m >= PREREQ_THRESHOLD:
                continue  # đã nắm vững → không phải "mới"
            if i == 0:
                ranked.append((t, f"'{t.name}' là chủ đề mở đầu — bắt đầu hành trình tại đây."))
            else:
                prev = ordered[i - 1]
                prev_m = _mastery_of(prev.id, mastery_map)
                if prev_m >= PREREQ_THRESHOLD:
                    ranked.append((
                        t,
                        f"Bạn đã nắm '{prev.name}' ({round(prev_m * 100)}% ≥ 70%) — "
                        f"sẵn sàng học chủ đề mới '{t.name}'.",
                    ))
        if not ranked:  # prerequisite chưa đạt ở đâu → gợi ý topic đầu chưa thành thạo
            unmastered = [t for t in ordered if _mastery_of(t.id, mastery_map) < PREREQ_THRESHOLD]
            t = unmastered[0] if unmastered else ordered[-1]
            ranked.append((t, f"Hãy củng cố '{t.name}' trước khi mở khóa chủ đề tiếp theo."))

    else:  # "exam" và mặc định: ưu tiên topic mastery thấp nhất
        by_weak = sorted(ordered, key=lambda t: _mastery_of(t.id, mastery_map))
        for t in by_weak:
            pct = round(_mastery_of(t.id, mastery_map) * 100)
            ranked.append((t, f"Ôn thi: '{t.name}' mastery {pct}% — củng cố các chủ đề yếu trước kỳ thi."))

    out = []
    for t, reason in ranked[:n]:
        p = _mastery_of(t.id, mastery_map)
        out.append({
            "topic": t,
            "p_mastery": p,
            "percent": round(p * 100, 1),
            "reason": reason,
        })
    return out


def recommend_topic(
    topics: list[Topic],
    mastery_map: dict[int, float],
    goal_type: str,
) -> Topic | None:
    """Topic tốt nhất để học tiếp (đầu danh sách gợi ý)."""
    recs = recommend_topics(topics, mastery_map, goal_type, n=1)
    return recs[0]["topic"] if recs else None


def _recently_attempted_qids(
    session: Session, user_id: int, within: timedelta = RECENT_WINDOW
) -> set[int]:
    cutoff = datetime.utcnow() - within
    rows = session.exec(
        select(Attempt.question_id).where(
            Attempt.user_id == user_id, Attempt.attempted_at >= cutoff
        )
    ).all()
    return set(rows)


def select_question(
    session: Session,
    topic_id: int,
    theta: float,
    *,
    user_id: int | None = None,
    exclude_qids: set[int] | None = None,
) -> Question | None:
    """IRT adaptive: pick câu trong topic có |difficulty_b − theta| nhỏ nhất.

    Loại các câu trong `exclude_qids` và (nếu có `user_id`) các câu đã làm trong
    24h gần nhất. Nếu sau khi loại không còn câu → relax filter (chỉ giữ
    exclude_qids của session hiện tại), cuối cùng fallback bất kỳ câu nào.
    """
    questions = session.exec(
        select(Question).where(Question.topic_id == topic_id)
    ).all()
    if not questions:
        return None

    exclude = set(exclude_qids or set())
    recent = _recently_attempted_qids(session, user_id) if user_id is not None else set()

    def _closest(pool: list[Question]) -> Question | None:
        if not pool:
            return None
        return min(pool, key=lambda q: abs(q.difficulty_b - theta))

    # 1) Loại cả recent lẫn exclude.
    primary = [q for q in questions if q.id not in exclude and q.id not in recent]
    pick = _closest(primary)
    if pick is not None:
        return pick

    # 2) Relax: chỉ loại câu trong session hiện tại.
    relaxed = [q for q in questions if q.id not in exclude]
    pick = _closest(relaxed)
    if pick is not None:
        return pick

    # 3) Fallback: bất kỳ câu nào của topic.
    return _closest(questions)
