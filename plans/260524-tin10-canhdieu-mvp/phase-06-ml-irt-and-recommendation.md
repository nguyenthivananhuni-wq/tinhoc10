# Phase 06 — ML: IRT 1-PL & Recommendation Engine (Tuần 6)

## Context links

- Parent: [plan.md](./plan.md)
- Source: [BRAINSTORM.md](../../BRAINSTORM.md) §5.2 (IRT), §5.4 (recommendation logic)
- Reference: [reports/04-ml-algorithms.md](./reports/04-ml-algorithms.md) §IRT
- Depends on: P02 (User.ability_theta, Question.difficulty_b), P04 (Attempt history), P05 (mastery vector).
- Blocks: P07 (clustering features cần ability + cluster recommendation).

## Overview

- **Date:** 2026-05-24
- **Description:** Implement IRT 1-PL (Rasch) — estimate user ability θ + calibrate question difficulty b. Adaptive question selection chọn câu có b ≈ θ. Recommendation engine combine BKT mastery + goal_type + IRT.
- **Priority:** P0 (báo cáo ML)
- **Implementation status:** Done (2026-05-29)
- **Review status:** tests pass (test_irt.py, test_recommender.py, test_calibrate.py)

## Key Insights

- Rasch 1-PL chỉ có 1 param khó (b) — đơn giản hơn 2-PL/3-PL, đủ defendable.
- Ability estimate dùng MLE đơn giản: gradient descent vài chục step hoặc closed-form approx.
- Difficulty calibration cần ≥30 response/câu → KHỞI ĐẦU b=0 cho tất cả, recalibrate batch sau khi có data.
- Adaptive selection: target `|θ - b| < 0.5` để tối đa Fisher info (Rasch: max info ở θ=b).
- Recommendation = rule-based filter (theo goal) + IRT pick (adaptive câu trong topic chọn).
- Không cần re-estimate θ sau MỖI câu — re-estimate sau quiz session đủ (giảm latency).

## Requirements

### Functional
- Module `app/ml/irt.py` — function `estimate_ability(responses)` + `prob_correct(theta, b)`.
- Module `app/ml/recommender.py` — function `recommend_topic(user, mastery_vector, goal)` + `select_question(user, topic_id)`.
- Script `scripts/calibrate_difficulty.py` — batch recalibrate `Question.difficulty_b` từ Attempt history (chạy thủ công).
- Modify `POST /quiz/answer` — sau session end, re-estimate θ → update User.ability_theta.
- Modify `GET /quiz/{topic_id}` — dùng `select_question()` thay random.
- Endpoint `GET /recommend` — show 3 recommendation cho user.
- Unit test IRT: ≥4 case.

### Non-functional
- `estimate_ability` < 200ms cho 100 response.
- `select_question` < 50ms.
- Recommendation explain text (vì sao recommend topic này) cho UX.

## Architecture

```
app/
  ml/
    irt.py             ← prob_correct, estimate_ability (MLE)
    recommender.py     ← rule-based + IRT picker
  routers/
    recommend.py       ← GET /recommend
    quiz.py            ← modified to use select_question
scripts/
  calibrate_difficulty.py  ← offline batch
tests/
  test_irt.py
  test_recommender.py
```

```
End of quiz session:
  responses = [(question_b, is_correct), ...]
  θ_new = estimate_ability(responses)
  user.ability_theta = θ_new

Start of new quiz:
  topic = recommender.recommend_topic(user, mastery, goal)
  question = recommender.select_question(user, topic) 
             → find q in topic with |b - θ| min
```

## Related code files

| File | Purpose |
|---|---|
| `app/ml/irt.py` | Rasch math + MLE |
| `app/ml/recommender.py` | Topic + question picker |
| `app/routers/recommend.py` | /recommend endpoint |
| `app/routers/quiz.py` | Modified select_question |
| `scripts/calibrate_difficulty.py` | Batch b calibration |
| `tests/test_irt.py` | Unit tests |
| `tests/test_recommender.py` | Rule tests |
| `app/templates/recommend.html` | Show 3 suggestions |

## Implementation Steps

### Learning tasks (~4h)

1. **L1:** Rasch model intro — blog/Wikipedia (1.5h).
2. **L2:** MLE concept (gradient descent log-likelihood) (1h).
3. **L3:** Đọc lại recommendation logic trong BRAINSTORM §5.4 (30m).
4. **L4:** numpy basics — vectorize, exp, log (1h).

### Coding tasks (~10h)

**IRT core (3h)**
5. **C1:** `irt.py` — `prob_correct(theta, b)` = `1 / (1 + np.exp(-(theta - b)))` (15m).
6. **C2:** `log_likelihood(theta, responses)` — sum log(p) cho correct + log(1-p) cho incorrect (30m).
7. **C3:** `estimate_ability(responses, max_iter=50, lr=0.1)` — gradient ascent (1h).
8. **C4:** Edge case: empty responses → return 0.0; all correct → cap +3.0; all wrong → cap -3.0 (30m).
9. **C5:** Manual REPL test với 10 response mix (45m).

**Unit tests (1.5h)**
10. **C6:** `test_irt.py` — case 1: prob_correct(0, 0) = 0.5 (15m).
11. **C7:** Case 2: 10/10 correct on b=0 → θ tăng > 0 (15m).
12. **C8:** Case 3: 0/10 correct on b=0 → θ < 0 (15m).
13. **C9:** Case 4: 5/10 correct on b=0 → θ ≈ 0 (tolerance 0.3) (15m).
14. **C10:** Case 5: vector consistency với BRAINSTORM example (15m).
15. **C11:** Add pytest CI script (15m).

**Recommender (3h)**
16. **C12:** `recommender.recommend_topic(user, mastery_dict, goal)` — implement 4 branch (exam/new_topic/improve/challenge) theo BRAINSTORM §5.4 (1h).
17. **C13:** `recommender.select_question(user, topic_id, session)` — query Question where topic_id, exclude attempted (last 24h), order by `abs(difficulty_b - user.ability_theta)`, limit 1 (1h).
18. **C14:** Fallback: nếu không còn câu chưa làm → relax filter (30m).
19. **C15:** Generate explain text — "Bạn yếu chủ đề X (mastery 35%), nên học bù" (30m).

**Integration (2h)**
20. **C16:** Modify `quiz.py` GET /quiz: nếu user có ability_theta → dùng select_question (45m).
21. **C17:** Modify POST /quiz/answer end-of-session: estimate θ, update User.ability_theta (45m).
22. **C18:** Endpoint `routers/recommend.py` GET /recommend — render 3 recommendation (30m).

**Calibration (1.5h)**
23. **C19:** `scripts/calibrate_difficulty.py` — query Attempt group by question_id, compute accuracy rate, derive b ≈ -log(p/(1-p)) (45m).
24. **C20:** Add CLI arg --dry-run, print changes (30m).
25. **C21:** Test calibration script trên DB dev với data từ P04+P05 quiz (15m).

## Todo list

- [ ] L1: Rasch model
- [ ] L2: MLE concept
- [ ] L3: Re-read BRAINSTORM §5.4
- [ ] L4: numpy basics
- [ ] C1: prob_correct
- [ ] C2: log_likelihood
- [ ] C3: estimate_ability MLE
- [ ] C4: Edge cases
- [ ] C5: REPL test
- [ ] C6-C10: 5 unit tests
- [ ] C11: pytest CI
- [ ] C12: recommend_topic 4 branches
- [ ] C13: select_question
- [ ] C14: Fallback no questions left
- [ ] C15: Explain text
- [ ] C16: quiz.py adaptive
- [ ] C17: End-session theta update
- [ ] C18: /recommend endpoint
- [ ] C19: calibrate script
- [ ] C20: --dry-run flag
- [ ] C21: Test calibration

## Success Criteria

- IRT unit tests pass (≥4 case).
- User làm 10 câu mix → ability_theta cập nhật, không stuck 0.
- Câu hỏi tiếp theo có |b - θ| < câu trước (adaptive verify).
- /recommend trả 3 topic kèm explain text.
- Calibration script chạy → ≥1 câu có b ≠ 0 sau khi có data.
- 2 user yếu vs giỏi → recommend khác nhau (demo case).

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| MLE không converge → θ NaN | HIGH | Cap θ ∈ [-4, 4], fallback last good value |
| Adaptive chọn cùng câu (đã làm) | MED | Exclude question_ids trong Attempt 24h gần nhất |
| Recommendation conflict mastery thấp + challenge goal | MED | Goal priority, không silent fallback |
| Calibration b sai khi <10 response | MED | Skip câu có <10 response, giữ b=0 |
| User mới ability_theta=0 → câu b=0 toàn dễ | LOW | Khởi đầu force difficulty_level=1 cho 5 câu đầu |

## Security Considerations

- /recommend yêu cầu auth.
- Calibration script chỉ chạy local/admin — KHÔNG expose endpoint.
- User.ability_theta không leak qua API (chỉ internal).
- Input validation: question_id phải tồn tại + thuộc topic_id request.

## Open Questions

- Adaptive selection có cần explore-exploit balance (ε-greedy random 10%) để tránh stuck?
- θ user có cần per-topic (4 vector) hay 1 global θ?
- Recommendation 3 hay 5?
- Calibration tự động chạy cron daily hay manual?

## Next steps

Phase 07 — K-means clustering + dashboard polish + deploy + báo cáo cuối.
