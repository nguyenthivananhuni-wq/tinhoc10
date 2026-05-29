"""Bayesian Knowledge Tracing (BKT) — pure math, no DB.

Citation: Corbett, A. T., & Anderson, J. R. (1995). "Knowledge tracing:
Modeling the acquisition of procedural knowledge." User Modeling and
User-Adapted Interaction, 4(4), 253-278.

Standard 4-parameter BKT per skill:
    P(L0) — prior probability student knows skill before any practice.
    P(T)  — probability of transitioning from "not known" to "known" per opportunity.
    P(G)  — probability of guessing correctly while not knowing.
    P(S)  — probability of slipping (answering incorrectly while knowing).

Update rule (per observation):

    Step 1 — Posterior P(L_t | obs):
        if correct:    numer = P(L_t) * (1 - P(S))
                       denom = numer + (1 - P(L_t)) * P(G)
        else:          numer = P(L_t) * P(S)
                       denom = numer + (1 - P(L_t)) * (1 - P(G))

        P(L_t | obs) = numer / denom

    Step 2 — Apply transition:
        P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)

Output is clamped to [0.0, 1.0].
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BktParams:
    """4 BKT parameters. Defaults are from Corbett & Anderson (1995)."""

    p_l0: float = 0.1   # initial knowledge
    p_t: float = 0.2    # transition (learning rate)
    p_g: float = 0.2    # guess
    p_s: float = 0.1    # slip

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name}={val} must be in [0, 1]")


DEFAULT_PARAMS = BktParams()


def posterior_given_evidence(
    prev_p: float, is_correct: bool, params: BktParams = DEFAULT_PARAMS
) -> float:
    """P(L_t | observation) via Bayes' rule. Does NOT apply transition."""
    if is_correct:
        numer = prev_p * (1.0 - params.p_s)
        denom = numer + (1.0 - prev_p) * params.p_g
    else:
        numer = prev_p * params.p_s
        denom = numer + (1.0 - prev_p) * (1.0 - params.p_g)

    if denom <= 0.0:
        return prev_p
    return numer / denom


def update_mastery(
    prev_p: float, is_correct: bool, params: BktParams = DEFAULT_PARAMS
) -> float:
    """One BKT step: combine evidence posterior with transition. Returns clamped [0, 1]."""
    posterior = posterior_given_evidence(prev_p, is_correct, params)
    new_p = posterior + (1.0 - posterior) * params.p_t
    return max(0.0, min(1.0, new_p))


def predict_correct(p_mastery: float, params: BktParams = DEFAULT_PARAMS) -> float:
    """Probability the student answers correctly given current mastery.

    P(correct) = P(L) * (1 - P(S)) + (1 - P(L)) * P(G)
    """
    return p_mastery * (1.0 - params.p_s) + (1.0 - p_mastery) * params.p_g
