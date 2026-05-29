# Report 02 — Database Schema

> Reference cho Phase 02. 6 bảng. SQLite + SQLModel.

## Overview

```
User ──< Attempt >── Question >── Topic ──┐
  └──< MasteryState >── Topic              │
  └──< LearningGoal                        │
                                           │
                          Topic.parent_id ─┘ (self-ref, nullable)
```

## SQL DDL (reference, SQLModel sẽ auto-gen)

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ability_theta REAL NOT NULL DEFAULT 0.0,
    is_admin INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_user_username ON user(username);

CREATE TABLE topic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    order_in_syllabus INTEGER NOT NULL,
    parent_id INTEGER NULL REFERENCES topic(id),
    description TEXT NULL
);

CREATE TABLE question (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL REFERENCES topic(id),
    content TEXT NOT NULL,
    difficulty_level INTEGER NOT NULL CHECK(difficulty_level IN (1,2,3)),
    type TEXT NOT NULL DEFAULT 'mcq' CHECK(type IN ('mcq','short')),
    difficulty_b REAL NOT NULL DEFAULT 0.0,
    options_json TEXT NOT NULL,       -- JSON array string
    correct_answer TEXT NOT NULL,
    source_page TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_question_topic ON question(topic_id);
CREATE INDEX idx_question_difficulty ON question(topic_id, difficulty_level);

CREATE TABLE attempt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    question_id INTEGER NOT NULL REFERENCES question(id),
    is_correct INTEGER NOT NULL,         -- 0/1
    response_time_ms INTEGER NOT NULL DEFAULT 0,
    selected_answer TEXT NULL,
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT NULL                  -- group attempts per quiz session
);
CREATE INDEX idx_attempt_user_time ON attempt(user_id, attempted_at);
CREATE INDEX idx_attempt_question ON attempt(question_id);
CREATE INDEX idx_attempt_session ON attempt(session_id);

CREATE TABLE mastery_state (
    user_id INTEGER NOT NULL REFERENCES user(id),
    topic_id INTEGER NOT NULL REFERENCES topic(id),
    p_mastery REAL NOT NULL DEFAULT 0.1,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, topic_id)
);

CREATE TABLE learning_goal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    goal_type TEXT NOT NULL CHECK(goal_type IN ('exam','new_topic','improve','challenge')),
    set_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_goal_user_active ON learning_goal(user_id, is_active);
```

## SQLModel classes (reference)

```python
# app/models/user.py
from datetime import datetime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=20)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ability_theta: float = 0.0
    is_admin: bool = False
```

```python
# app/models/topic.py
class Topic(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    order_in_syllabus: int
    parent_id: int | None = Field(default=None, foreign_key="topic.id")
    description: str | None = None
```

```python
# app/models/question.py
class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    content: str
    difficulty_level: int = Field(ge=1, le=3)
    type: str = "mcq"
    difficulty_b: float = 0.0
    options_json: str               # JSON-encoded list
    correct_answer: str
    source_page: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

```python
# app/models/attempt.py
class Attempt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    is_correct: bool
    response_time_ms: int = 0
    selected_answer: str | None = None
    attempted_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    session_id: str | None = Field(default=None, index=True)
```

```python
# app/models/mastery.py
class MasteryState(SQLModel, table=True):
    __tablename__ = "mastery_state"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    topic_id: int = Field(foreign_key="topic.id", primary_key=True)
    p_mastery: float = 0.1
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

```python
# app/models/goal.py
class LearningGoal(SQLModel, table=True):
    __tablename__ = "learning_goal"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    goal_type: str                     # exam|new_topic|improve|challenge
    set_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
```

## Indexes summary

| Index | Bảng | Cột | Lý do |
|---|---|---|---|
| idx_user_username | user | username | login lookup |
| idx_question_topic | question | topic_id | quiz query |
| idx_question_difficulty | question | (topic_id, difficulty_level) | adaptive select |
| idx_attempt_user_time | attempt | (user_id, attempted_at) | history |
| idx_attempt_question | attempt | question_id | calibration |
| idx_attempt_session | attempt | session_id | quiz result agg |
| idx_goal_user_active | learning_goal | (user_id, is_active) | get current goal |

## Seed Topics (initial)

| id | name | order_in_syllabus |
|---|---|---|
| 1 | Mạng máy tính và Internet | 1 |
| 2 | Dữ liệu, thông tin và xử lý thông tin | 2 |
| 3 | Python cơ bản | 3 |
| 4 | Lập trình giải bài toán | 4 |

## Migration strategy

- Dev: drop file `data/app.db` rồi `init_db()` lại nếu đổi schema.
- Production: KHÔNG drop (sẽ mất data) — accept hoặc dùng Alembic (out of scope MVP).

## Unresolved questions

- `is_admin` flag trên User hay hardcoded admin username?
- `options_json` lưu TEXT string hay dùng `sa_column=Column(JSON)`?
- LearningGoal: 1 active per user hay history list (multiple rows, is_active flag)?
- Có cần bảng `Session` riêng để track quiz session (start/end time, total questions)?
