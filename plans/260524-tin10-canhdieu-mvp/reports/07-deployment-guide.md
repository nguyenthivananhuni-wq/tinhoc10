# Report 07 — Deployment Guide (Render.com)

> Reference cho Phase 07. Deploy MVP lên URL public.

## Tại sao Render.com

- Free tier có Python runtime sẵn.
- Auto-deploy từ GitHub.
- HTTPS auto-enable.
- Deploy chỉ tốn 5 phút.
- Alternative: Railway (cũng OK, syntax tương tự).

## Limitations free tier Render

| Limit | Value | Impact |
|---|---|---|
| Cold start | ~30s sau 15 phút idle | Demo cần warm-up |
| Persistent disk | Không free | SQLite file MẤT khi redeploy |
| Bandwidth | 100GB/month | Đủ thừa |
| Compute hours | 750h/month | 1 service luôn on được |
| CPU/RAM | 0.5 CPU, 512MB RAM | Đủ MVP |

**SQLite mất data** → 2 options:
- A. Accept reseed mỗi deploy (chấp nhận cho demo concept). 
- B. Render persistent disk $7/month (skip cho MVP).
- C. Switch sang Postgres free tier (Supabase/Neon) — out of scope.

## Files cần thêm

### `requirements.txt`
```
fastapi==0.110.0
uvicorn[standard]==0.27.0
sqlmodel==0.0.16
passlib[bcrypt]==1.7.4
itsdangerous==2.1.2
jinja2==3.1.3
python-multipart==0.0.9
scikit-learn==1.4.0
numpy==1.26.0
markdown==3.5.2
```

### `Procfile` (option 1)
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### `render.yaml` (option 2 — preferred, infra-as-code)
```yaml
services:
  - type: web
    name: tin10-canhdieu
    env: python
    region: singapore
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SESSION_SECRET
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: APP_ENV
        value: production
```

### `runtime.txt` (optional, lock Python)
```
python-3.11.0
```

## Env vars

| Key | Value | Where |
|---|---|---|
| `SESSION_SECRET` | (random 32 char) | Render dashboard, generateValue |
| `PYTHON_VERSION` | `3.11.0` | render.yaml |
| `APP_ENV` | `production` | render.yaml |
| `DATABASE_URL` | `sqlite:///data/app.db` | (default, app code) |

## App code adjustments cho production

### `app/main.py`
```python
import os
from fastapi import FastAPI

is_prod = os.getenv("APP_ENV") == "production"

app = FastAPI(
    title="Tin học 10 Cánh Diều",
    docs_url=None if is_prod else "/docs",   # disable swagger prod
    redoc_url=None,
)

@app.on_event("startup")
def on_startup():
    from app.seed import init_db, seed_topics, seed_questions, seed_demo_users
    init_db()
    seed_topics()
    seed_questions()
    if is_prod and os.getenv("SEED_DEMO") == "1":
        seed_demo_users()
```

### `app/security.py`
```python
import os
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-only-secret-do-not-use-in-prod")
COOKIE_SECURE = os.getenv("APP_ENV") == "production"
```

### Cookie config khi set
```python
response.set_cookie(
    key="session",
    value=token,
    max_age=60*60*24*7,
    httponly=True,
    secure=COOKIE_SECURE,
    samesite="lax",
)
```

## Deploy steps

1. **Setup GitHub repo:**
   ```
   git init
   git remote add origin git@github.com:<you>/tin10.git
   git add .
   git push -u origin main
   ```

2. **Render dashboard:**
   - New → Web Service → Connect GitHub repo.
   - Region: Singapore (gần VN).
   - Build command: `pip install -r requirements.txt`.
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
   - Plan: Free.
   - Add env vars (SESSION_SECRET, APP_ENV).

3. **First deploy:**
   - Watch logs.
   - Common error: `bcrypt` build fail → đảm bảo `passlib[bcrypt]` pinned 1.7.4.
   - Verify `https://tin10-canhdieu.onrender.com/` trả về landing.

4. **Post-deploy verification checklist:**
   - [ ] Landing page load.
   - [ ] Register + login flow OK.
   - [ ] Quiz 1 câu submit không 500.
   - [ ] Dashboard radar chart render.
   - [ ] `/docs` trả về 404 (disabled prod).
   - [ ] Cookie `secure=True` trong DevTools.
   - [ ] Seed data có (4 topic, 120 câu HOẶC fallback 40).

## Warm-up cho demo

Cold start 30s khó chịu khi demo trực tiếp → 2 cách:
- A. Ping endpoint `/` từ UptimeRobot mỗi 10 phút trước demo (free).
- B. Mở tab Render dashboard 5 phút trước demo, manual visit URL.

## Troubleshooting

| Issue | Fix |
|---|---|
| Build fail bcrypt | Pin `passlib[bcrypt]==1.7.4`, không upgrade |
| SQLite read-only | Mount path `/data` không có quyền — dùng path relative `./data/` trong app code |
| Static file 404 | `app.mount("/static", StaticFiles(directory="app/static"))` |
| HTMX CDN block | Fallback unpkg.com |
| Module not found | Check `app/__init__.py` exist + run command `uvicorn app.main:app` (không `python app/main.py`) |
| Port không bind | Use `$PORT` env, không hardcode 8000 |

## Rollback plan

- Render giữ deploy history → click "Rollback to previous" 1 click.
- DB lost on rollback → seed lại từ startup hook.

## Demo URL

Sau deploy, URL dạng: `https://tin10-canhdieu.onrender.com`

Bookmark cho báo cáo + video demo.

## Unresolved questions

- Render vs Railway final choice?
- Có cần custom domain (`tin10.<your-name>.com`)?
- Persistent disk $7/mo cho production-grade hay accept reseed?
- Setup CI GitHub Actions (lint, test) trước deploy hay manual?
- Logging service (Sentry free, Logtail) cho monitor errors prod?
