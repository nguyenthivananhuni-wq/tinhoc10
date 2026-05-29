# Phase 01 — Foundation Setup (Tuần 1)

## Context links

- Parent: [plan.md](./plan.md)
- Source: [BRAINSTORM.md](../../BRAINSTORM.md) §4 (tech stack), §10 (next steps)
- Blocks: tất cả phases sau (cần env Python + project scaffold).
- Depends on: nothing.

## Overview

- **Date:** 2026-05-24
- **Description:** Setup môi trường dev, học Python cơ bản, FastAPI hello world, project scaffold sẵn cho coding.
- **Priority:** P0 (foundation)
- **Implementation status:** Not Started
- **Review status:** pending

## Key Insights

- Dev mới chỉ biết HTML/CSS/JS → Python tutorial PHẢI focused, không học OOP nâng cao/decorator/async sâu.
- FastAPI auto-docs Swagger UI → dùng test endpoint từ tuần 1, không cần Postman.
- Virtualenv vs `venv` builtin: dùng `venv` để bớt 1 tool.
- Windows path separator gotcha: dùng `pathlib.Path` thay vì hardcode `\` hoặc `/`.

## Requirements

### Functional
- App "hello world" chạy local trên `http://127.0.0.1:8000`.
- 1 endpoint `GET /` trả về JSON `{"status": "ok"}`.
- 1 endpoint `GET /hello/{name}` test path param.
- Swagger UI `/docs` truy cập được.
- Auto-reload khi save file (uvicorn `--reload`).

### Non-functional
- Project structure khớp BRAINSTORM §10.
- requirements.txt pin version (FastAPI, uvicorn, SQLModel, passlib, itsdangerous, jinja2, sklearn, numpy).
- README ngắn (cách chạy local).
- Git init (optional nhưng nên).

## Architecture

```
/Tin_hoc10
  /app
    main.py          ← FastAPI app instance + 2 endpoint hello
    /routers         ← empty (sẽ thêm phase 04)
    /models          ← empty (phase 02)
    /ml              ← empty (phase 05+)
    /templates       ← empty (phase 04)
    /static          ← empty
  /data              ← empty
  /tests             ← empty (or skip)
  /plans             ← exist
  requirements.txt
  README.md
  .gitignore
  venv/              ← gitignored
```

## Related code files

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI app + hello endpoints |
| `requirements.txt` | Pin dependencies |
| `.gitignore` | venv, __pycache__, .db, .env |
| `README.md` | Quick start commands |
| `app/__init__.py` | Mark package |

## Implementation Steps

### Learning tasks (Day 1-3, ~6h)

1. **L1:** Install Python 3.11 + VSCode Python extension (30m).
2. **L2:** W3Schools Python tutorial — variables, types, list, dict, if/for, function, import (2h).
3. **L3:** Đọc FastAPI tutorial first-steps + path-parameters + query-parameters (2h).
4. **L4:** Hiểu `venv`: tạo, activate trên PowerShell, install package (30m).
5. **L5:** Đọc HTMX intro page (1h, optional cho phase này).

### Coding tasks (Day 4-7, ~6h)

6. **C1:** Tạo `venv` và activate (15m).
7. **C2:** Viết `requirements.txt` với pinned versions (15m).
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
   ```
8. **C3:** `pip install -r requirements.txt` (15m).
9. **C4:** Tạo folder structure (15m).
10. **C5:** Viết `app/main.py` với 2 endpoint hello (30m).
11. **C6:** Run `uvicorn app.main:app --reload` và verify `/` + `/docs` (15m).
12. **C7:** Viết `.gitignore` + `README.md` ngắn (30m).
13. **C8:** `git init` + commit đầu tiên (15m, optional).

## Todo list

- [ ] L1: Install Python 3.11 + VSCode
- [ ] L2: Python basics (W3Schools)
- [ ] L3: FastAPI tutorial first-steps
- [ ] L4: venv usage
- [ ] L5: HTMX intro (optional)
- [ ] C1: Create venv
- [ ] C2: Write requirements.txt
- [ ] C3: pip install
- [ ] C4: Folder structure
- [ ] C5: main.py with hello endpoints
- [ ] C6: Verify uvicorn runs
- [ ] C7: .gitignore + README
- [ ] C8: git init (optional)

## Success Criteria

- `uvicorn app.main:app --reload` chạy không error.
- Browser `http://127.0.0.1:8000/` → `{"status":"ok"}`.
- `http://127.0.0.1:8000/docs` hiển thị Swagger UI với 2 endpoint.
- `pip freeze` match `requirements.txt`.
- Dev tự explain được "FastAPI là gì, decorator `@app.get` làm gì".

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Python install lỗi PATH Windows | LOW | Tick "Add Python to PATH" khi install |
| pip install bcrypt fail Windows | MED | Dùng `passlib[bcrypt]==1.7.4` + có thể cần Visual C++ Build Tools |
| Học Python lan man qua OOP/async | MED | Stick với W3Schools, skip class/decorator nâng cao |
| uvicorn port 8000 busy | LOW | `--port 8001` |

## Security Considerations

- Không hardcode secret vào main.py.
- `.gitignore` `venv/`, `*.db`, `.env`.
- Phase này chưa có auth/data nên security risk thấp.

## Open Questions

- Pytest setup từ phase 01 hay defer tới phase 04?
- Dùng `python-dotenv` cho config hay hardcode trong phase đầu?

## Next steps

Phase 02 — Database & Models: thiết kế schema, viết SQLModel classes, init DB file, seed structure (chưa seed data thật).
