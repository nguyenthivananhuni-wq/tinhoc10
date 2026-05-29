# Report 03 — API Routes

> Reference cho Phase 04 + 06 + 07. All routes.

## Convention

- HTML routes return Jinja2 template (`TemplateResponse`).
- HTMX partial routes return small HTML fragment (header `HX-Request`).
- Auth dep: `current_user = Depends(get_current_user)` raises 401 nếu cookie invalid.
- Admin dep: `current_admin = Depends(require_admin)`.

## Group 1 — Auth

| Method | Path | Auth | Request | Response | Purpose |
|---|---|---|---|---|---|
| GET | `/register` | none | - | register.html | Show register form |
| POST | `/register` | none | form: username, password, password2 | redirect /login HOẶC register.html with error | Create user |
| GET | `/login` | none | - | login.html | Show login form |
| POST | `/login` | none | form: username, password | redirect /goal or /dashboard + Set-Cookie | Auth |
| POST | `/logout` | session | - | redirect / + Clear-Cookie | End session |

## Group 2 — Pages (read-only)

| Method | Path | Auth | Response | Purpose |
|---|---|---|---|---|
| GET | `/` | optional | landing.html | Hero page |
| GET | `/topics` | session | topic_list.html (4 topic + count câu) | List topics |
| GET | `/theory/{topic_id}` | session | theory.html (MD render) | Read theory |
| GET | `/history` | session | history.html (paginated Attempt) | Past attempts |
| GET | `/dashboard` | session | dashboard.html (radar + recommend card) | User analytics |

## Group 3 — Goal & Quiz

| Method | Path | Auth | Request | Response | Purpose |
|---|---|---|---|---|---|
| GET | `/goal` | session | - | goal_select.html | Show goal form |
| POST | `/goal` | session | form: goal_type | redirect /topics | Save LearningGoal |
| GET | `/quiz/{topic_id}` | session | query ?n=10 | quiz.html (1 câu đầu) | Start quiz session |
| POST | `/quiz/answer` | session | form: question_id, selected_answer, response_time_ms, session_id | _quiz_card.html partial (next câu) HOẶC redirect result | Submit + next |
| GET | `/quiz/result/{session_id}` | session | - | quiz_result.html | Final score |
| GET | `/recommend` | session | - | recommend.html (3 suggestion) | Show recommendations |

## Group 4 — Admin

| Method | Path | Auth | Response | Purpose |
|---|---|---|---|---|
| GET | `/admin/clusters` | admin | admin_clusters.html (scatter PCA) | View clusters |
| POST | `/admin/clusters/refresh` | admin | redirect /admin/clusters | Rerun K-means |
| POST | `/admin/seed_demo` | admin | redirect /admin | Create demo users |
| POST | `/admin/calibrate` | admin | redirect /admin | Run difficulty calibration |

## Group 5 — Static

| Path | Purpose |
|---|---|
| `/static/js/quiz_timer.js` | Response time JS |
| `/static/img/*` | Logo, illustrations |
| `/docs` | Swagger UI (disable in prod via `docs_url=None`) |

## Request/Response examples

### POST /register
```
Form: username=alice&password=secret123&password2=secret123
Success → 303 See Other, Location: /login
Error → 200 + register.html với `error="Username đã tồn tại"`
```

### POST /quiz/answer (HTMX)
```
Headers: HX-Request: true
Form: question_id=42&selected_answer=B&response_time_ms=8500&session_id=abc-123
Response: 200 + HTML partial _quiz_card.html (câu tiếp)
HOẶC nếu hết câu: HX-Redirect header → /quiz/result/abc-123
```

### GET /dashboard
```
Cookie: session=<signed>
Response: dashboard.html với context:
{
  "user": User,
  "mastery": {1: 0.45, 2: 0.72, 3: 0.30, 4: 0.55},
  "topic_names": ["Mạng & Internet", "Dữ liệu", "Python", "Lập trình"],
  "ability_theta": 0.3,
  "cluster_label": "Trung bình",
  "recommendations": [...]
}
```

## Error handling

| Code | When |
|---|---|
| 200 | Success (HTMX swap) |
| 303 | Redirect after POST (PRG pattern) |
| 401 | Cookie invalid/missing → redirect /login |
| 403 | Admin route, user not admin |
| 404 | Topic/Question không tồn tại |
| 422 | Form validation lỗi (FastAPI auto) |
| 500 | Internal — log + render error.html |

## Auth check pseudo-code

```python
async def get_current_user(request: Request, session: Session = Depends(get_session)):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        data = serializer.loads(token, max_age=3600 * 24 * 7)
    except BadSignature:
        raise HTTPException(401, "Invalid session")
    user = session.get(User, data["user_id"])
    if not user:
        raise HTTPException(401, "User not found")
    return user

def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return user
```

## Unresolved questions

- Cần endpoint JSON API riêng (mobile/external) hay chỉ HTML?
- Rate limit endpoint /login (brute-force protection)?
- API versioning `/v1/...` cần không (MVP có thể skip)?
- Endpoint export attempt CSV cho user?
