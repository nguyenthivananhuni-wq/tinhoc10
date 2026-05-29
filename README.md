# Hệ thống hỗ trợ học Tin học 10 - Cánh Diều

Web app cá nhân hóa lộ trình học Tin 10 (Cánh Diều) — học sinh làm quiz, hệ thống dùng **BKT**, **IRT 1-PL**, **K-means** để theo dõi mastery + gợi ý bài tiếp theo.

**Stack:** Python 3.11 · FastAPI · SQLite · SQLModel · Jinja2 · HTMX · Tailwind CDN · Chart.js CDN · scikit-learn

## Tài liệu

- [BRAINSTORM.md](./BRAINSTORM.md) — quyết định kiến trúc + scope
- [plans/260524-tin10-canhdieu-mvp/](./plans/260524-tin10-canhdieu-mvp/) — implementation plan chi tiết (7 phases + 7 reports)

## Quick start (sau khi cài Python 3.11)

### 1. Tạo virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> Nếu PowerShell báo lỗi execution policy:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 2. Cài dependencies

```powershell
pip install -r requirements.txt
```

### 3. Chạy dev server

```powershell
uvicorn app.main:app --reload
```

Mở browser:
- http://127.0.0.1:8000/ → `{"status":"ok",...}`
- http://127.0.0.1:8000/hello/Anh → `{"message":"Xin chào Anh!"}`
- http://127.0.0.1:8000/docs → Swagger UI (test endpoints trực tiếp)

### 4. Chạy tests (khi có ML modules)

```powershell
pytest -v
```

## Cấu trúc thư mục

```
Tin_hoc10/
├── app/
│   ├── main.py          # FastAPI app entry
│   ├── routers/         # API endpoints (phase 04+)
│   ├── models/          # SQLModel classes (phase 02)
│   ├── ml/              # BKT, IRT, K-means (phase 05-07)
│   ├── templates/       # Jinja2 HTML (phase 04+)
│   └── static/          # CSS, JS, images
├── data/                # SQLite DB + seed JSON
├── tests/               # Pytest cho ML modules
├── plans/               # Implementation plans (do not delete)
├── requirements.txt
├── BRAINSTORM.md
└── README.md
```

## Roadmap

| Phase | Mục tiêu | Tuần |
|---|---|---|
| 01 ✅ | Foundation setup | 1 |
| 02 | Database + SQLModel | 2 |
| 03 | Content production (soạn câu hỏi) | 3 parallel |
| 04 | Auth + Quiz engine HTMX | 4 |
| 05 | BKT mastery + radar chart | 5 |
| 06 | IRT 1-PL + adaptive recommendation | 6 |
| 07 | K-means + dashboard + deploy | 7-8 |
