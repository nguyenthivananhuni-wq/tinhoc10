"""Bridge between BKT pure math and the database (MasteryState rows).

Single entry point: `apply_bkt_for_attempt(...)` — call after inserting an Attempt.
"""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.ml.bkt import DEFAULT_PARAMS, BktParams, update_mastery
from app.models import MasteryState, Question


def get_or_create_mastery(
    user_id: int,
    topic_id: int,
    session: Session,
    initial_p: float | None = None,
) -> MasteryState:
    """Return the MasteryState row for (user, topic), creating it lazily with P(L0)."""
    row = session.get(MasteryState, (user_id, topic_id))
    if row is not None:
        return row
    initial_p = DEFAULT_PARAMS.p_l0 if initial_p is None else initial_p
    row = MasteryState(user_id=user_id, topic_id=topic_id, p_mastery=initial_p)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def apply_bkt_for_attempt(
    user_id: int,
    question_id: int,
    is_correct: bool,
    session: Session,
    params: BktParams = DEFAULT_PARAMS,
) -> tuple[float, float]:
    """Run one BKT update for the topic the question belongs to.

    Returns (prev_p, new_p) for logging/debugging.
    """
    question = session.get(Question, question_id)
    if question is None:
        raise ValueError(f"Question {question_id} not found")

    mastery = get_or_create_mastery(user_id, question.topic_id, session)
    prev_p = mastery.p_mastery
    new_p = update_mastery(prev_p, is_correct, params)

    mastery.p_mastery = new_p
    mastery.last_updated = datetime.utcnow()
    session.add(mastery)
    session.commit()
    return prev_p, new_p


def mastery_vector(user_id: int, session: Session) -> dict[int, float]:
    """Return {topic_id: p_mastery} for all topics the user has any mastery row for."""
    rows = session.exec(
        select(MasteryState).where(MasteryState.user_id == user_id)
    ).all()
    return {r.topic_id: r.p_mastery for r in rows}
