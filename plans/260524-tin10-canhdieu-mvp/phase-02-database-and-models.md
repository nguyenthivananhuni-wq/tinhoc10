# Phase 02 — Database & Models (Tuần 2)

## Context links

- Parent: [plan.md](./plan.md)
- Source: [BRAINSTORM.md](../../BRAINSTORM.md) §4.4 (schema sơ bộ)
- Reference: [reports/02-database-schema.md](./reports/02-database-schema.md)
- Depends on: Phase 01 (env + scaffold).
- Blocks: P03 (cần Question/Topic schema để soạn seed), P04 (User/Attempt), P05 (MasteryState), P06 (Attempt history).

## Overview

- **Date:** 2026-05-24
- **Description:** Finalize DB schema, viết SQLModel classes, tạo DB file SQLite, seed Topic structure (chưa câu hỏi), config session/connection.
- **Priority:** P0 (block hầu hết phases)
- **Implementation status:** Not Started
- **Review status:** pending

## Key Insights

- SQLModel = SQLAlchemy + Pydantic → 1 class vừa làm table vừa làm validation.
- SQLite file path: dùng `pathlib.Path(__file__).parent.parent / "data" / "app.db"`.
- Foreign key trong SQLite cần `PRAGMA foreign_keys = ON` mỗi connection.
- Index: `(user_id, topic_id)` cho MasteryState, `(user_id, attempted_at)` cho Attempt.
- `options_json` lưu options MCQ dạng JSON string (SQLite không có JSON native trong SQLModel basic) — dùng `sa_column=Column(JSON)` hoặc TEXT + json.loads.
- Migration: không dùng Alembic (overkill) — drop+recreate DB nếu schema đổi trong dev.

## Requirements

### Functional
- 6 SQLModel classes: User, Topic, Question, Attempt, MasteryState, LearningGoal.
- Quan hệ FK chính xác (User-Attempt, Question-Topic, MasteryState-User-Topic).
- Default values: `ability_theta=0.0`, `difficulty_b=0.0`, `p_mastery=0.1`.
- Init function tạo DB file + tables nếu chưa tồn tại.
- Seed Topic data (4 topic mẫu, chưa câu hỏi).

### Non-functional
- Tất cả model trong `app/models/*.py` (1 file/model hoặc 1 file `models.py` gộp).
- Connection helper `app/db.py` với `get_session()` dependency.
- Index trên FK + timestamp.

## Architecture

```
app/
  db.py                ← engine + SessionLocal + get_session() dep
  models/
    __init__.py        ← re-export all models
    user.py
    topic.py
    question.py
    attempt.py
    mastery.py
    goal.py
  seed.py              ← init_db() + seed_topics()
data/
  app.db               ← SQLite file (gitignored)
```

```
User ──< Attempt >── Question >── Topic ──┐
  └──< MasteryState >── Topic              │
  └──< LearningGoal                        │
                                           │
                          Topic.parent_id ─┘ (self-ref, optional)
```

## Related code files

| File | Purpose |
|---|---|
| `app/db.py` | Engine, session factory, get_session dep |
| `app/models/user.py` | User table |
| `app/models/topic.py` | Topic + self-ref parent |
| `app/models/question.py` | Question + options_json |
| `app/models/attempt.py` | Attempt log |
| `app/models/mastery.py` | MasteryState composite key |
| `app/models/goal.py` | LearningGoal |
| `app/models/__init__.py` | Re-exports |
| `app/seed.py` | init_db + seed_topics |
| `app/main.py` | Hook `init_db()` on startup |

## Implementation Steps

### Learning tasks (~3h)

1. **L1:** Đọc SQLModel quickstart + relationships (1.5h).
2. **L2:** SQLite primer — file-based, không server (30m).
3. **L3:** Hiểu FastAPI Depends pattern cho session (1h).

### Coding tasks (~8h)

4. **C1:** Viết `app/db.py` với engine + `get_session()` (45m).
5. **C2:** Viết `User` model — id, username unique, password_hash, created_at, ability_theta (30m).
6. **C3:** Viết `Topic` model — id, name, order_in_syllabus, parent_id self-ref nullable (30m).
7. **C4:** Viết `Question` model — id, topic_id FK, content, difficulty_level (1-3), type, difficulty_b, options_json (TEXT), correct_answer (45m).
8. **C5:** Viết `Attempt` model — id, user_id FK, question_id FK, is_correct, response_time_ms, attempted_at, indexed `(user_id, attempted_at)` (30m).
9. **C6:** Viết `MasteryState` — composite PK `(user_id, topic_id)`, p_mastery, last_updated (45m).
10. **C7:** Viết `LearningGoal` — id, user_id FK, goal_type enum (exam/new_topic/improve/challenge), set_at (30m).
11. **C8:** `__init__.py` re-export tất cả (15m).
12. **C9:** Viết `init_db()` trong `seed.py` — `SQLModel.metadata.create_all(engine)` (30m).
13. **C10:** Viết `seed_topics()` — insert 4 Topic mẫu (theo report 05) nếu bảng rỗng (45m).
14. **C11:** Hook startup event trong `main.py` gọi `init_db()` (15m).
15. **C12:** Manual test — chạy app, mở DB bằng DB Browser for SQLite, verify tables + 4 topic (45m).
16. **C13:** Viết `tests/test_models.py` smoke test create User + query (optional, 1h).

## Todo list

- [ ] L1: SQLModel quickstart
- [ ] L2: SQLite primer
- [ ] L3: FastAPI Depends pattern
- [ ] C1: db.py engine + session
- [ ] C2: User model
- [ ] C3: Topic model
- [ ] C4: Question model
- [ ] C5: Attempt model
- [ ] C6: MasteryState model
- [ ] C7: LearningGoal model
- [ ] C8: models __init__ re-export
- [ ] C9: init_db()
- [ ] C10: seed_topics()
- [ ] C11: Hook startup event
- [ ] C12: Manual verify in DB Browser
- [ ] C13: Smoke test (optional)

## Success Criteria

- `python -c "from app.seed import init_db; init_db()"` tạo `data/app.db` với 6 bảng.
- DB Browser hiển thị 4 row trong Topic.
- Restart app không re-seed duplicate.
- Tạo manual 1 User + 1 Attempt qua SQL hoặc Python REPL không lỗi FK.

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Composite PK SQLModel cú pháp tricky | MED | Dùng `Field(primary_key=True)` trên cả 2 field |
| options_json type Column JSON | MED | Fallback TEXT + manual `json.dumps`/`loads` |
| Schema thay đổi giữa chừng | MED | Drop file `app.db` rồi rerun init_db (dev only) |
| FK constraints không enforce SQLite | LOW | Add `event.listens_for(Engine, "connect")` set `PRAGMA foreign_keys=ON` |

## Security Considerations

- `password_hash` field — chưa hash ở phase này (phase 04), nhưng KHÔNG để plaintext column.
- DB file `data/app.db` add vào `.gitignore`.
- Username unique constraint để tránh duplicate signup sau.

## Open Questions

- Có cần `updated_at` field tự động cho mọi bảng không?
- Topic.parent_id có thực sự dùng (sub-topic hierarchy) hay flat 4 topic là đủ?
- LearningGoal: 1 active per user hay history list?

## Next steps

Phase 03 (parallel) — soạn câu hỏi vào JSON. Phase 04 — auth + quiz endpoints sẽ consume schema này.
