# Report 01 — Tech Stack Rationale

> Tóm tắt từ [BRAINSTORM.md](../../../BRAINSTORM.md) §4 + §6. Reference khi viết báo cáo.

## Stack chốt

```
Backend:   Python 3.11 + FastAPI + SQLite + SQLModel
Frontend:  Jinja2 + HTMX + Tailwind CSS (CDN) + Chart.js (CDN)
ML:        scikit-learn + numpy (BKT/IRT tự code, K-means dùng sklearn)
Auth:      Session (passlib bcrypt + itsdangerous)
Deploy:    Render.com (free tier)
```

## Tại sao Python (không Node.js)

| Tiêu chí | Python | Node |
|---|---|---|
| ML libraries native | numpy/sklearn/scipy | yếu, phải tự code math |
| Khớp môn học SGK Tin 10 | dạy Python | không |
| FastAPI auto-docs Swagger | sẵn | phải Swagger UI riêng |
| Cost học (dev biết JS) | ~1 tuần | 0 (đã biết) |
| Báo cáo strength | mạnh ML | yếu ML |

**Verdict:** Chấp nhận 1 tuần học Python để có ML defendable trong báo cáo.

## Tại sao FastAPI (không Flask/Django)

- **Flask:** Quá tối thiểu, phải tự setup nhiều, không auto-docs.
- **Django:** Batteries-included nhưng overkill, ORM nặng, ít linh hoạt ML pipeline.
- **FastAPI:** Type hints + Pydantic + auto Swagger + async support + beginner-friendly.

## Tại sao HTMX (không React/Vue)

- Không build tool, không bundler, không npm.
- Server-render Jinja2 + attribute HTML (`hx-get`, `hx-post`).
- Học 1 buổi sáng vs React tốn 2-3 tuần.
- Phù hợp dev mới biết JS cơ bản.
- Demo concept không cần SPA UX.

## Tại sao SQLite (không Postgres)

- Demo concept, single-writer.
- File-based, không cần DB server.
- Render free tier không có Postgres free vĩnh viễn.
- SQLModel hỗ trợ tốt.
- **Tradeoff:** File mất khi redeploy Render → seed lại mỗi lần (acceptable demo).

## Tại sao Session-based auth (không OAuth)

- Tiết kiệm 3-5 ngày dev (đăng ký Google/Zalo OAuth, config callback URL).
- Không critical cho demo concept.
- passlib bcrypt + itsdangerous signed cookie = secure enough.

## Tại sao Tailwind CDN (không build)

- Không cần PostCSS, không cần npm build pipeline.
- 1 script tag `<script src="cdn.tailwindcss.com">` đủ.
- **Tradeoff:** Bundle size lớn hơn production-grade nhưng OK cho demo.

## Tại sao Chart.js (không D3/Plotly)

- Radar chart out-of-the-box.
- CDN 1 file.
- API đơn giản hơn D3.
- Đủ cho 2 chart cần (radar + scatter).

## Approaches Evaluated (rejected)

| Approach | Lý do reject |
|---|---|
| Frontend-only + localStorage | Không multi-device, không ML thật |
| Node.js + Express | ML stack yếu, báo cáo yếu |
| Django fullstack | Overkill, ORM nặng |
| Next.js + Python ML service | 2 service deploy phức tạp |

## Citations cho báo cáo

- **BKT:** Corbett, A. T., & Anderson, J. R. (1995). "Knowledge tracing: Modeling the acquisition of procedural knowledge." *User Modeling and User-Adapted Interaction*, 4(4), 253-278.
- **IRT Rasch:** Rasch, G. (1960). *Probabilistic Models for Some Intelligence and Attainment Tests.* Danmarks Pædagogiske Institut.
- **K-means:** MacQueen, J. (1967). "Some methods for classification and analysis of multivariate observations." *Berkeley Symposium*.

## Unresolved questions

- Có nên dùng `pyBKT` library thay tự code BKT (giảm code, kém defendable)?
- Render.com vs Railway final choice?
