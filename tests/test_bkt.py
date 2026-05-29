"""Unit tests for BKT pure math (no DB)."""
from __future__ import annotations

import pytest

from app.ml.bkt import (
    DEFAULT_PARAMS,
    BktParams,
    posterior_given_evidence,
    predict_correct,
    update_mastery,
)


# ---- BktParams ----

def test_default_params_match_paper():
    assert DEFAULT_PARAMS.p_l0 == 0.1
    assert DEFAULT_PARAMS.p_t == 0.2
    assert DEFAULT_PARAMS.p_g == 0.2
    assert DEFAULT_PARAMS.p_s == 0.1


def test_params_validation_rejects_out_of_range():
    with pytest.raises(ValueError):
        BktParams(p_l0=1.5)
    with pytest.raises(ValueError):
        BktParams(p_s=-0.1)
    with pytest.raises(ValueError):
        BktParams(p_g=2.0)


# ---- posterior_given_evidence ----

def test_posterior_correct_increases_belief():
    """Observing correct should raise the posterior compared to the prior."""
    prev = 0.3
    post = posterior_given_evidence(prev, is_correct=True)
    assert post > prev


def test_posterior_incorrect_decreases_belief():
    prev = 0.3
    post = posterior_given_evidence(prev, is_correct=False)
    assert post < prev


def test_posterior_at_one_remains_high_after_incorrect():
    """If we believe the student knows it (p=1), one incorrect should drop belief but not crash."""
    post = posterior_given_evidence(0.999, is_correct=False)
    assert 0.0 <= post <= 1.0


# ---- update_mastery: 5 paper-recommended test cases ----

def test_case_1_correct_raises_mastery():
    new_p = update_mastery(prev_p=0.1, is_correct=True)
    assert new_p > 0.1


def test_case_2_incorrect_keeps_relatively_low():
    """Single incorrect from p=0.1 ends up near the transition floor P(T)=0.2.

    The transition step adds (1 - posterior) * P(T), so even after a wrong answer
    mastery rises slightly to ~0.21 (not above ~0.25). Compared to a correct answer,
    it's much lower.
    """
    new_p_wrong = update_mastery(prev_p=0.1, is_correct=False)
    new_p_right = update_mastery(prev_p=0.1, is_correct=True)
    assert new_p_wrong < new_p_right
    # near-floor expectation: between p_t and p_t + small slop
    assert DEFAULT_PARAMS.p_t * 0.95 < new_p_wrong < 0.25


def test_case_3_five_correct_streak_reaches_high():
    """After 5 consecutive correct answers, mastery should exceed 0.85 (paper-typical)."""
    p = 0.1
    history = [p]
    for _ in range(5):
        p = update_mastery(p, is_correct=True)
        history.append(p)
    assert p > 0.85, f"after 5 correct streak, p={p:.4f}, history={history}"
    # And strictly monotone increasing
    for a, b in zip(history, history[1:]):
        assert b >= a, f"non-monotone: {history}"


def test_case_4_alternating_does_not_explode():
    """CICIC alternating should not converge to 0 or 1 — stays in a bounded mid-to-high range."""
    p = 0.1
    history = [p]
    for correct in [True, False, True, False, True]:
        p = update_mastery(p, is_correct=correct)
        history.append(p)
    # Doesn't explode to extremes
    assert 0.2 < p < 0.95, f"alternating reached p={p:.4f}, history={history}"
    # Compare to pure correct streak — must be strictly less
    p_streak = 0.1
    for _ in range(5):
        p_streak = update_mastery(p_streak, is_correct=True)
    assert p < p_streak, f"alternating p={p:.4f} >= streak p={p_streak:.4f}"


def test_case_5_near_one_correct_clamped():
    """At p=0.99, one more correct should not exceed 1.0."""
    new_p = update_mastery(prev_p=0.99, is_correct=True)
    assert new_p <= 1.0
    assert new_p > 0.9


def test_clamp_lower_bound():
    """At p=0.001, multiple incorrects should not go below 0."""
    p = 0.001
    for _ in range(10):
        p = update_mastery(p, is_correct=False)
    assert p >= 0.0


def test_transition_floor_after_observation():
    """Even if posterior collapses, transition guarantees floor of p_t for next step."""
    # An impossible perfect "guesser" scenario where posterior given incorrect goes very low
    p = update_mastery(prev_p=0.001, is_correct=False)
    # New p should be at least p_t (0.2) due to transition adding chance to learn
    assert p >= DEFAULT_PARAMS.p_t * 0.99  # tolerate float noise


# ---- predict_correct ----

def test_predict_correct_low_mastery_near_guess():
    """When mastery ~0, P(correct) ≈ P(G) = 0.2."""
    p = predict_correct(0.0)
    assert abs(p - DEFAULT_PARAMS.p_g) < 0.01


def test_predict_correct_high_mastery_near_one_minus_slip():
    """When mastery = 1, P(correct) = 1 - P(S) = 0.9."""
    p = predict_correct(1.0)
    assert abs(p - (1 - DEFAULT_PARAMS.p_s)) < 0.01


def test_predict_correct_midrange():
    p = predict_correct(0.5)
    # Should be between guess and (1 - slip)
    assert DEFAULT_PARAMS.p_g < p < (1 - DEFAULT_PARAMS.p_s)


# ---- Custom params ----

def test_custom_params_used():
    fast_params = BktParams(p_l0=0.1, p_t=0.5, p_g=0.1, p_s=0.05)
    slow = update_mastery(0.1, True, DEFAULT_PARAMS)
    fast = update_mastery(0.1, True, fast_params)
    assert fast > slow, "higher p_t should yield faster learning"
