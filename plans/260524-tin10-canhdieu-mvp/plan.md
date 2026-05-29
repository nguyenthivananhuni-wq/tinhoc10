# Plan — Hệ thống hỗ trợ học Tin học 10 Cánh Diều (MVP)

> Date: 2026-05-24 (260524) · Solo dev · <2 tháng · Demo concept với nhấn mạnh ML/AI

## Overview

Web app cá nhân hóa lộ trình học Tin 10 Cánh Diều: học sinh làm quiz → BKT cập nhật mastery → IRT chọn câu adaptive → K-means cluster học sinh → radar chart + recommendation.

**Stack chốt:** Python 3.11 · FastAPI · SQLite · SQLModel · Jinja2 · HTMX · Tailwind CDN · Chart.js CDN · scikit-learn · passlib · itsdangerous.

**Reference:** [BRAINSTORM.md](../../BRAINSTORM.md) — nguồn duy nhất, không đổi stack/scope.

## Phases

| # | Phase | File | Tuần | Status | Progress |
|---|---|---|---|---|---|
| 01 | foundation-setup | [phase-01-foundation-setup.md](./phase-01-foundation-setup.md) | 1 | Done | 100% |
| 02 | database-and-models | [phase-02-database-and-models.md](./phase-02-database-and-models.md) | 2 | Done | 100% |
| 03 | content-production | [phase-03-content-production.md](./phase-03-content-production.md) | 3 (parallel 4-6) | Done | 100% |
| 04 | auth-and-quiz-engine | [phase-04-auth-and-quiz-engine.md](./phase-04-auth-and-quiz-engine.md) | 4 | Done | 100% |
| 05 | ml-bkt-mastery | [phase-05-ml-bkt-mastery.md](./phase-05-ml-bkt-mastery.md) | 5 | Done | 100% |
| 06 | ml-irt-and-recommendation | [phase-06-ml-irt-and-recommendation.md](./phase-06-ml-irt-and-recommendation.md) | 6 | Done | 100% |
| 07 | ml-clustering-dashboard-deploy | [phase-07-ml-clustering-dashboard-deploy.md](./phase-07-ml-clustering-dashboard-deploy.md) | 7-8 | Code Done | 90% |
| 08 | ui-redesign + teacher-panel (ngoài plan gốc) | [project-roadmap](../../docs/project-roadmap.md) | — | Done | 100% |

> **Cập nhật 2026-05-29:** Sau P07 đã làm thêm (ngoài plan gốc): redesign toàn bộ UI theme tím + sidebar, panel giáo viên (overview/students/questions/clusters), trang /profile, auth 401→/login, hardening prod. 156 tests pass. Chi tiết: [docs/project-roadmap.md](../../docs/project-roadmap.md).

## Critical Path

```
P01 → P02 → P04 → P05 → P06 → P07
              ↑
           P03 (parallel, blocks seed của P04)
```

- P02 schema block hầu hết các phase sau.
- P03 (soạn câu hỏi) **chạy song song** P04/P05/P06 — không đợi.
- P05 cần Attempt data → block P06 calibration sơ bộ.
- P07 cần ≥3 user data → demo cluster.

## Reports (reference)

- [01-tech-stack-rationale.md](./reports/01-tech-stack-rationale.md)
- [02-database-schema.md](./reports/02-database-schema.md)
- [03-api-routes.md](./reports/03-api-routes.md)
- [04-ml-algorithms.md](./reports/04-ml-algorithms.md)
- [05-content-production-plan.md](./reports/05-content-production-plan.md)
- [06-frontend-pages.md](./reports/06-frontend-pages.md)
- [07-deployment-guide.md](./reports/07-deployment-guide.md)

## Top 3 Risks

1. **Soạn 120 câu hỏi tốn 2+ tuần** (HIGH) → fallback 2 chủ đề × 20 câu = 40 câu.
2. **Beginner học Python+FastAPI chậm** (MEDIUM) → tutorial focused 1 tuần, không lan man framework khác.
3. **BKT/IRT params calibration sai** (MEDIUM) → dùng default từ paper, recalibrate sau data thật.

## Resolved Decisions (v2 — 2026-05-24)

| # | Câu hỏi | Quyết định | Ghi chú |
|---|---|---|---|
| 1 | Deploy host | **Render.com** | Free 750h/tháng, Python template sẵn, beginner-friendly |
| 2 | BKT implementation | **Tự code ~80 dòng** | Defendable trong defense; Bayes' rule không khó |
| 3 | Tests | **Pytest cho ML modules** | BKT/IRT/K-means có unit tests; routes/auth skip |
| 4 | Câu hỏi format | **Chỉ MCQ 4 đáp án** | Không có short answer |
| 5 | Khi nào show đáp án | **Ngay sau mỗi câu** (default) | Better learning UX + BKT update incrementally |

## Open Questions (còn lại)

- Embed YouTube minh họa lý thuyết — có hay không? (low priority, có thể quyết sau)
- Số câu/quiz session: fix 5, 10, hay user chọn? (đề xuất: fix 10 câu)

## Review Status

- Plan version: v2 (2026-05-24) — resolved 5 open questions
- Reviewer: pending user final approval
