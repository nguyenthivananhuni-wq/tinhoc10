"""Item Response Theory — 1-PL (Rasch) model. Pure math, no DB.

Citation: Rasch, G. (1960). "Probabilistic Models for Some Intelligence and
Attainment Tests." Danish Institute for Educational Research. Foundation of
modern adaptive testing (TOEFL/GMAT CAT).

Model:
    P(correct | theta, b) = 1 / (1 + exp(-(theta - b)))

    theta — student ability (latent trait).
    b     — item difficulty.

Ability estimation uses Maximum Likelihood via gradient ascent on the
log-likelihood. The gradient of the log-likelihood w.r.t. theta is:

    dLL/dtheta = sum_i ( y_i - p_i )

where y_i ∈ {0, 1} is the observed response and p_i = sigmoid(theta - b_i).

For all-correct or all-wrong response sets the MLE diverges to ±infinity, so
we clamp theta to a sensible range and short-circuit those degenerate cases.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

# Ability is bounded to keep estimates finite and avoid numerical overflow.
THETA_MIN = -4.0
THETA_MAX = 4.0
# Degenerate (all-correct / all-wrong) sets get a softer cap than the hard
# clamp so a perfect run does not look identical to the numerical limit.
THETA_ALL_CORRECT = 3.0
THETA_ALL_WRONG = -3.0


def prob_correct(theta: float, b: float = 0.0) -> float:
    """P(correct) under the Rasch model = sigmoid(theta - b)."""
    z = theta - b
    # Numerically stable logistic.
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def log_likelihood(theta: float, responses: Sequence[tuple[float, bool]]) -> float:
    """Sum of log P(observed) over responses = [(b, is_correct), ...]."""
    eps = 1e-12
    total = 0.0
    for b, is_correct in responses:
        p = prob_correct(theta, b)
        total += math.log(p + eps) if is_correct else math.log(1.0 - p + eps)
    return total


def _clamp(theta: float) -> float:
    return max(THETA_MIN, min(THETA_MAX, theta))


def estimate_ability(
    responses: Sequence[tuple[float, bool]],
    *,
    max_iter: int = 50,
    lr: float = 0.1,
    tol: float = 1e-5,
) -> float:
    """Estimate ability theta by gradient ascent on the log-likelihood.

    Args:
        responses: list of (difficulty_b, is_correct).
        max_iter: max gradient steps.
        lr: learning rate.
        tol: stop when the gradient magnitude drops below this.

    Returns:
        Estimated theta, clamped to [THETA_MIN, THETA_MAX]. Empty input → 0.0.
        All-correct → THETA_ALL_CORRECT, all-wrong → THETA_ALL_WRONG.
    """
    if not responses:
        return 0.0

    n_correct = sum(1 for _, c in responses if c)
    if n_correct == len(responses):
        return THETA_ALL_CORRECT
    if n_correct == 0:
        return THETA_ALL_WRONG

    theta = 0.0
    for _ in range(max_iter):
        gradient = sum(
            (1.0 if is_correct else 0.0) - prob_correct(theta, b)
            for b, is_correct in responses
        )
        theta += lr * gradient
        theta = _clamp(theta)
        if abs(gradient) < tol:
            break

    return _clamp(theta)
