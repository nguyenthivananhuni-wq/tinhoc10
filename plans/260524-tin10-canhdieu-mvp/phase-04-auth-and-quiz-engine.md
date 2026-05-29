# Phase 04 — Auth & Quiz Engine (Tuần 4)

## Context links

- Parent: [plan.md](./plan.md)
- Source: [BRAINSTORM.md](../../BRAINSTORM.md) §3 (session-based auth), §4 (HTMX), §9 (week 4)
- Reference: [reports/03-api-routes.md](./reports/03-api-routes.md), [reports/06-frontend-pages.md](./reports/06-frontend-pages.md)
- Depends on: P01 (env), P02 (User/Question/Attempt), P03 (seed data — soft dep, có thể test với mock data)
- Blocks: P05 (cần Attempt records để chạy BKT).

## Overview

- **Date:** 2026-05-24
- **Description:** Đăng ký/đăng nhập session, chọn learning goal, làm quiz HTMX (1 câu/lần), submit answer → lưu Attempt, xem kết quả.
- **Priority:** P0
- **Implementation status:** Not Started
- **Review status:** pending

## Key Insights

- Session-based: lưu `user_id` trong cookie ký HMAC bằng `itsdangerous.URLSafeSerializer`.
- HTMX flow quiz: server render 1 câu, `hx-post` submit → server return next câu hoặc result.
- Quiz state: lưu trong DB (Attempt rows) thay vì session để tránh lost on refresh.
- Password hash: passlib bcrypt rounds=12 (default).
- Login form: `python-multipart` cần cho parse form data trong FastAPI.
- CSRF: với same-origin form + SameSite=Lax cookie → đủ cho demo (không add CSRF token middleware).
- Tailwind CDN script tag trong base.html → không cần build.

## Requirements

### Functional
- `POST /register` — username + password, hash bcrypt, insert User, redirect login.
- `POST /login` — verify hash, set session cookie, redirect goal-select.
- `POST /logout` — clear cookie.
- `GET /goal` — form chọn learning goal (4 options).
- `POST /goal` — save LearningGoal row.
- `GET /quiz/{topic_id}` — start quiz, lấy câu đầu (random hoặc difficulty 1).
- `POST /quiz/answer` — htmx submit, lưu Attempt, return next câu hoặc finish partial.
- `GET /quiz/result/{session_id}` — show số đúng/sai + link dashboard.
- Pages: landing, register, login, goal-select, topic-list, quiz, quiz-result, history.

### Non-functional
- Password min 6 chars.
- Session cookie HttpOnly + SameSite=Lax + Secure (cho production HTTPS).
- All form POST endpoints require auth (except /register, /login).
- `response_time_ms` đo từ render → submit (JS timestamp đính kèm form).

## Architecture

```
app/
  routers/
    auth.py            ← /register /login /logout
    quiz.py            ← /quiz/* /goal
    pages.py           ← /, /topics, /history (GET only)
  security.py          ← hash_password, verify_password, sign_session, get_current_user dep
  templates/
    base.html          ← Tailwind CDN, HTMX CDN
    landing.html
    register.html
    login.html
    goal_select.html
    topic_list.html
    quiz.html
    _quiz_card.html    ← partial cho HTMX swap
    quiz_result.html
    history.html
  static/
    js/quiz_timer.js
```

```
[Browser] ──hx-post /quiz/answer──> [FastAPI]
                                         │ verify session cookie
                                         │ insert Attempt
                                         │ pick next question (random P04; adaptive P06)
                                         ▼
                                    [_quiz_card.html partial swap]
```

## Related code files

| File | Purpose |
|---|---|
| `app/routers/auth.py` | Register/login/logout |
| `app/routers/quiz.py` | Quiz flow + goal |
| `app/routers/pages.py` | Landing, topic list, history |
| `app/security.py` | Hash, session sign, auth dep |
| `app/templates/*.html` | All Jinja templates |
| `app/static/js/quiz_timer.js` | Response time tracking |
| `app/main.py` | Mount routers, register middleware |

## Implementation Steps

### Learning tasks (~5h)

1. **L1:** Đọc FastAPI security tutorial (cookie auth) (1h).
2. **L2:** Đọc HTMX `hx-post` + `hx-target` + `hx-swap` (1h).
3. **L3:** Đọc Tailwind utility classes cơ bản (flex/grid/spacing/colors) (1h).
4. **L4:** Jinja2 template inheritance + include partial (1h).
5. **L5:** passlib + itsdangerous quickstart (1h).

### Coding tasks (~14h)

**Auth (4h)**
6. **C1:** `security.py` — `hash_password()`, `verify_password()`, `sign_session(user_id)`, `unsign_session()` (1h).
7. **C2:** `get_current_user()` Depends — đọc cookie, decode, query User, raise 401 nếu invalid (45m).
8. **C3:** `routers/auth.py` — POST /register validate username unique, hash, insert (45m).
9. **C4:** POST /login verify, set cookie, redirect (45m).
10. **C5:** POST /logout clear cookie (15m).
11. **C6:** `templates/register.html` + `login.html` form Tailwind (45m).

**Pages & Goal (3h)**
12. **C7:** `base.html` với Tailwind CDN + HTMX CDN + navbar (45m).
13. **C8:** `landing.html` hero + CTA login/register (30m).
14. **C9:** `goal_select.html` form 4 radio + POST handler (45m).
15. **C10:** `topic_list.html` GET /topics list 4 topic + button start quiz (45m).
16. **C11:** `history.html` GET /history list Attempt gần nhất (30m).

**Quiz Flow (5h)**
17. **C12:** GET /quiz/{topic_id} init quiz, pick câu hỏi đầu (random difficulty 1 ở phase này), render `quiz.html` (1h).
18. **C13:** `_quiz_card.html` partial: question content + 4 options radio + hidden response_time field (45m).
19. **C14:** `static/js/quiz_timer.js` — set `data-start` khi render, on submit ghi `(Date.now() - start)` vào hidden field (45m).
20. **C15:** POST /quiz/answer parse form, insert Attempt, query next câu hoặc end (1.5h).
21. **C16:** GET /quiz/result/{session_id} — agg correct/total từ Attempt (45m).
22. **C17:** `quiz_result.html` + button "Xem dashboard" / "Làm lại" (15m).

**Wire up (2h)**
23. **C18:** Register routers trong `main.py`, mount static, setup Jinja2Templates (30m).
24. **C19:** Manual e2e test: register → login → goal → quiz 5 câu → result → history (1h).
25. **C20:** Optional: pytest 2-3 case auth (1h).

## Todo list

- [ ] L1-L5: Learning
- [ ] C1: security helpers
- [ ] C2: get_current_user dep
- [ ] C3: /register
- [ ] C4: /login
- [ ] C5: /logout
- [ ] C6: register+login templates
- [ ] C7: base.html
- [ ] C8: landing.html
- [ ] C9: goal_select
- [ ] C10: topic_list
- [ ] C11: history
- [ ] C12: GET /quiz init
- [ ] C13: _quiz_card partial
- [ ] C14: quiz_timer.js
- [ ] C15: POST /quiz/answer
- [ ] C16: GET /quiz/result
- [ ] C17: quiz_result template
- [ ] C18: main.py wire-up
- [ ] C19: e2e manual test
- [ ] C20: pytest (optional)

## Success Criteria

- Đăng ký user mới → login → cookie set.
- Cookie persistent qua refresh trang.
- Logout xóa cookie.
- Làm 5 câu quiz → DB có 5 Attempt với đúng user_id + response_time_ms > 0.
- Sai mật khẩu → error message hiện trong form.
- HTMX swap quiz card mượt, không full-page reload.
- `quiz_result` show đúng số đúng/tổng.

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Cookie không set trên localhost | MED | Set `secure=False` cho dev, `secure=True` prod |
| HTMX swap không trigger | MED | Verify `hx-target`/`hx-swap` đúng, check Network tab |
| `response_time_ms` thiếu (JS không gửi) | LOW | Default 0 nếu null, log warning |
| Race condition double-submit | LOW | Disable button on submit (HTMX `hx-disabled-elt`) |
| bcrypt slow trên Render free tier | LOW | Rounds=12 ổn, đo nếu >500ms thì giảm 10 |

## Security Considerations

- Password hash bcrypt (KHÔNG md5/sha256 raw).
- Cookie: HttpOnly + SameSite=Lax.
- Session secret key từ env var `SESSION_SECRET`, fallback random nếu dev.
- SQL injection: SQLModel ORM tự escape, KHÔNG concat string SQL.
- XSS: Jinja2 autoescape mặc định ON (KHÔNG `|safe` user content).
- Username regex `^[a-zA-Z0-9_]{3,20}$` ngăn injection trong URL.
- Rate limit login: nice-to-have (skip MVP), note cho future.

## Open Questions

- Quiz session = 5 câu, 10 câu, hay user chọn?
- Cho phép guest mode (không cần login) làm demo quiz không?
- Show đáp án đúng ngay sau mỗi câu hay đợi end-of-quiz?
- Goal đổi được sau khi set không?

## Next steps

Phase 05 — BKT mastery: dùng Attempt data đã sinh ra để cập nhật MasteryState + radar chart.
