# Phase 05 — ML: BKT Mastery & Radar Chart (Tuần 5)

## Context links

- Parent: [plan.md](./plan.md)
- Source: [BRAINSTORM.md](../../BRAINSTORM.md) §5.1 (BKT spec), §9 (week 5)
- Reference: [reports/04-ml-algorithms.md](./reports/04-ml-algorithms.md) §BKT
- Depends on: P02 (MasteryState schema), P04 (Attempt data).
- Blocks: P06 (recommendation cần mastery vector), P07 (dashboard hiển thị radar).

## Overview

- **Date:** 2026-05-24
- **Description:** Implement Bayesian Knowledge Tracing — sau mỗi Attempt update P(mastery) cho topic tương ứng. Radar chart hiển thị mastery 4 topic.
- **Priority:** P0 (báo cáo ML core)
- **Implementation status:** Not Started
- **Review status:** pending

## Key Insights

- BKT params default từ paper Corbett & Anderson 1995: P(L₀)=0.1, P(T)=0.2, P(G)=0.2, P(S)=0.1.
- Update rule **per skill/topic** — không cross-topic.
- Pure Python ~80 dòng → đừng dùng pyBKT nếu muốn báo cáo "tự implement" (tăng điểm defendable).
- MasteryState row tạo lazy — chỉ insert khi user lần đầu attempt câu thuộc topic đó.
- Radar chart Chart.js: data array 4 phần tử `[mastery_t1, mastery_t2, mastery_t3, mastery_t4]` ×100.
- Test BKT bằng 5 case cụ thể (correct streak vs alternating) — viết unit test trước khi tích hợp.

## Requirements

### Functional
- Module `app/ml/bkt.py` với class `BKT` hoặc function `update_mastery(prev_p, is_correct, params)`.
- Function `apply_bkt_for_attempt(user_id, question_id, is_correct, session)` — fetch MasteryState, update, save.
- Hook vào endpoint `POST /quiz/answer` (P04) — sau insert Attempt → call apply_bkt.
- Endpoint `GET /dashboard` render mastery 4 topic.
- Radar chart Chart.js trong dashboard.html.
- Unit test BKT: ≥5 test case khẳng định update math đúng.

### Non-functional
- BKT update <50ms (đơn giản, không vấn đề).
- Mastery clamp [0.0, 1.0].
- Log mastery delta để debug (optional).

## Architecture

```
app/
  ml/
    __init__.py
    bkt.py             ← pure math, no DB
    bkt_service.py     ← bridge DB ↔ bkt
  routers/
    dashboard.py       ← GET /dashboard
  templates/
    dashboard.html     ← Chart.js radar
tests/
  test_bkt.py
```

```
Attempt insert (P04)
       │
       ▼
bkt_service.apply_bkt_for_attempt()
       │
       ├── fetch MasteryState (or create with P(L₀)=0.1)
       ├── bkt.update_mastery(prev_p, is_correct)
       └── save MasteryState
       
Dashboard GET /dashboard
       │
       ▼
query MasteryState for current user
       │
       ▼
render template with JSON for Chart.js
```

## Related code files

| File | Purpose |
|---|---|
| `app/ml/bkt.py` | Pure BKT math + class |
| `app/ml/bkt_service.py` | DB integration |
| `app/routers/dashboard.py` | GET /dashboard |
| `app/templates/dashboard.html` | Radar chart + per-topic table |
| `tests/test_bkt.py` | Unit test 5+ cases |
| `app/routers/quiz.py` | Modified: call apply_bkt after Attempt insert |

## Implementation Steps

### Learning tasks (~4h)

1. **L1:** Đọc paper Corbett & Anderson 1995 (skim) hoặc blog explain BKT (1.5h).
2. **L2:** Hiểu Bayes' rule áp dụng cho BKT (whiteboard derivation) (1h).
3. **L3:** Chart.js radar chart docs + 1 example (1h).
4. **L4:** pytest basics (30m).

### Coding tasks (~9h)

**BKT core (3h)**
5. **C1:** Skeleton `app/ml/bkt.py` — `@dataclass BktParams(p_l0=0.1, p_t=0.2, p_g=0.2, p_s=0.1)` (15m).
6. **C2:** Function `_posterior_given_evidence(prev_p, is_correct, params)` — Bayes update conditional on observation (45m).
7. **C3:** Function `update_mastery(prev_p, is_correct, params)` — posterior + transition (P(T)) (45m).
   ```
   p_evidence = p * (1 - p_s) + (1 - p) * p_g  (nếu correct)
              = p * p_s + (1 - p) * (1 - p_g) (nếu incorrect)
   p_posterior = (correct: p * (1-p_s) / p_evidence; incorrect: p * p_s / p_evidence)
   p_new = p_posterior + (1 - p_posterior) * p_t
   ```
8. **C4:** Clamp output [0, 1] + docstring (15m).
9. **C5:** Manual REPL test 3 scenario (start=0.1, all correct 5 lần) (30m).

**Unit tests (1.5h)**
10. **C6:** `tests/test_bkt.py` setup pytest (15m).
11. **C7:** Test case 1: 1 correct → mastery tăng (15m).
12. **C8:** Test case 2: 1 incorrect → mastery giảm (15m).
13. **C9:** Test case 3: 5 correct streak → mastery → ~0.9+ (15m).
14. **C10:** Test case 4: alternating CICIC → mastery ổn định mid range (15m).
15. **C11:** Test case 5: edge p=0.999 correct → vẫn <=1 (15m).

**DB integration (2h)**
16. **C12:** `bkt_service.py` — `get_or_create_mastery(user_id, topic_id, session)` (45m).
17. **C13:** `apply_bkt_for_attempt(user_id, question_id, is_correct, session)` — lookup topic từ question, call update (45m).
18. **C14:** Hook trong `POST /quiz/answer` sau Attempt insert (30m).

**Dashboard + chart (2.5h)**
19. **C15:** `routers/dashboard.py` GET /dashboard query MasteryState, build dict `{topic_name: p_mastery}` (45m).
20. **C16:** `dashboard.html` extend base + canvas radar chart + table dưới (1h).
21. **C17:** Chart.js init script với data inline từ Jinja (45m).
22. **C18:** Test e2e — quiz 10 câu → check dashboard mastery 4 topic thay đổi (30m).

## Todo list

- [ ] L1: BKT paper/blog
- [ ] L2: Bayes derivation
- [ ] L3: Chart.js radar
- [ ] L4: pytest basics
- [ ] C1: BktParams dataclass
- [ ] C2: _posterior_given_evidence
- [ ] C3: update_mastery
- [ ] C4: Clamp + docstring
- [ ] C5: Manual REPL test
- [ ] C6: pytest setup
- [ ] C7-C11: 5 test cases
- [ ] C12: get_or_create_mastery
- [ ] C13: apply_bkt_for_attempt
- [ ] C14: Hook quiz/answer
- [ ] C15: dashboard router
- [ ] C16: dashboard.html
- [ ] C17: Chart.js init
- [ ] C18: e2e test

## Success Criteria

- 5+ unit test pass.
- Sau 5 câu đúng liên tiếp topic 1: mastery topic 1 ≥ 0.9.
- Radar chart 4 axis, scale 0-100.
- Dashboard load <500ms cho user có 50 Attempt.
- Mastery vector của 2 user khác nhau sau cùng quiz → khác nhau (verify diversity).

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Formula Bayes sai → mastery weird | HIGH | Unit test trước, so sánh kết quả với paper example |
| Mastery stuck ở 0.1 nếu lookup topic sai | MED | Log topic_id mỗi update, verify FK |
| Chart.js không render (CDN block) | LOW | Local fallback hoặc unpkg mirror |
| Mastery oscillate quá mạnh | LOW | Default params đã smooth, không cần tune |

## Security Considerations

- Endpoint `/dashboard` yêu cầu auth (current_user dep).
- Không leak mastery user khác — luôn filter `user_id = current_user.id`.
- Mastery value không phải PII nhưng vẫn private cho user đó.

## Open Questions

- Mastery có nên reset nếu user inactive > X ngày (forget curve)?
- Hiển thị mastery dạng % hay 5-star rating?
- Có nên expose BKT params per-topic (calibrate) hay global?
- Dùng `pyBKT` library (tradeoff: ít code hơn nhưng kém defendable trong báo cáo)?

## Next steps

Phase 06 — IRT 1-PL: tính ability θ + adaptive question selection dùng mastery + difficulty_b.
