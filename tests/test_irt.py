"""Unit tests for IRT 1-PL (Rasch) math."""
from __future__ import annotations

import math

import pytest

from app.ml.irt import (
    THETA_ALL_CORRECT,
    THETA_ALL_WRONG,
    THETA_MAX,
    THETA_MIN,
    estimate_ability,
    log_likelihood,
    prob_correct,
)


# ---- prob_correct ----

def test_prob_correct_at_theta_equals_b_is_half():
    assert prob_correct(0.0, 0.0) == pytest.approx(0.5)
    assert prob_correct(1.5, 1.5) == pytest.approx(0.5)


def test_prob_correct_monotonic_in_theta():
    assert prob_correct(-2, 0) < prob_correct(0, 0) < prob_correct(2, 0)


def test_prob_correct_harder_item_lowers_prob():
    # Same ability, harder item (bigger b) → lower P(correct).
    assert prob_correct(1.0, 0.0) > prob_correct(1.0, 2.0)


def test_prob_correct_numerically_stable_extremes():
    assert 0.0 < prob_correct(-50, 0) < 1e-10
    assert 1.0 - prob_correct(50, 0) < 1e-10


# ---- log_likelihood ----

def test_log_likelihood_higher_for_consistent_theta():
    # A strong student (theta=2) explains an all-correct set better than theta=-2.
    responses = [(0.0, True)] * 5
    assert log_likelihood(2.0, responses) > log_likelihood(-2.0, responses)


# ---- estimate_ability ----

def test_estimate_empty_returns_zero():
    assert estimate_ability([]) == 0.0


def test_estimate_all_correct_caps_high():
    assert estimate_ability([(0.0, True)] * 10) == THETA_ALL_CORRECT


def test_estimate_all_wrong_caps_low():
    assert estimate_ability([(0.0, False)] * 10) == THETA_ALL_WRONG


def test_estimate_half_correct_near_zero():
    responses = [(0.0, i % 2 == 0) for i in range(10)]  # 5 correct, 5 wrong on b=0
    theta = estimate_ability(responses)
    assert abs(theta) < 0.3


def test_estimate_mostly_correct_positive():
    # 8/10 correct on b=0 → ability above average.
    responses = [(0.0, i < 8) for i in range(10)]
    theta = estimate_ability(responses)
    assert theta > 0.0
    assert THETA_MIN <= theta <= THETA_MAX


def test_estimate_mostly_wrong_negative():
    responses = [(0.0, i < 2) for i in range(10)]  # 2/10 correct
    assert estimate_ability(responses) < 0.0


def test_estimate_harder_items_imply_higher_ability():
    # Same hit rate (5/10) but on harder items → higher ability estimate.
    easy = [(-1.0, i % 2 == 0) for i in range(10)]
    hard = [(1.0, i % 2 == 0) for i in range(10)]
    assert estimate_ability(hard) > estimate_ability(easy)


def test_estimate_stays_within_bounds():
    responses = [(b, c) for b in (-2, -1, 0, 1, 2) for c in (True, False)]
    theta = estimate_ability(responses)
    assert THETA_MIN <= theta <= THETA_MAX
    assert not math.isnan(theta)
