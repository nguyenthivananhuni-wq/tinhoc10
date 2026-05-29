# Phase 07 — K-means Clustering, Dashboard, Theory Pages & Deploy (Tuần 7-8)

## Context links

- Parent: [plan.md](./plan.md)
- Source: [BRAINSTORM.md](../../BRAINSTORM.md) §5.3 (K-means), §8 (success metrics demo), §9 (week 7-8)
- Reference: [reports/04-ml-algorithms.md](./reports/04-ml-algorithms.md) §K-means, [reports/07-deployment-guide.md](./reports/07-deployment-guide.md)
- Depends on: P05 (mastery), P06 (ability θ), P03 (content done hoặc fallback).
- Blocks: nothing (cuối project).

## Overview

- **Date:** 2026-05-24
- **Description:** K-means cluster 3 nhóm học sinh (yếu/TB/giỏi), dashboard analytics, theory pages, polish UI, deploy Render.com, viết báo cáo + record demo video.
- **Priority:** P0 (delivery cuối)
- **Implementation status:** Code Done (2026-05-29) — còn lại tác vụ thủ công (deploy Render thật, quay video, export PDF báo cáo)
- **Review status:** tests pass (test_clustering.py — 15 case)

## Key Insights

- K=3 fixed (matching 3 nhóm trong spec) — KHÔNG dùng elbow method để chọn k cho demo.
- Features: avg_mastery, avg_response_time_ms, total_attempts, accuracy_difficulty_3 (4D vector).
- Cluster RUN ON DEMAND (admin trigger), không real-time.
- Need ≥3 user để cluster có ý nghĩa → tạo 3-5 user giả với pattern khác nhau cho demo.
- PCA 2D cho scatter plot báo cáo.
- Render free tier: SQLite file mất khi container restart → cảnh báo trong báo cáo HOẶC dùng Render persistent disk ($).
- Báo cáo cần screenshots tốt — chuẩn bị scenario demo trước.

## Requirements

### Functional
- Module `app/ml/clustering.py` — `build_features(users)` + `cluster_users(features, k=3)`.
- Endpoint `GET /admin/clusters` — show 3 cluster với scatter plot PCA (admin only).
- Endpoint `GET /admin/seed_demo` — tạo 3 user demo với attempt pattern khác nhau (chỉ chạy nếu DB empty).
- Theory pages: GET /theory/{topic_id} render Markdown từ `data/theory/topic-XX.md`.
- Polish dashboard: thêm card "Cluster của bạn" + recommendation từ P06.
- History page enhancement: filter theo topic, paging.
- Deploy Render.com với URL public.
- Báo cáo PDF + video demo 3-5 phút.

### Non-functional
- Cluster job <1s cho 100 user.
- Theory page render Markdown → HTML (dùng `markdown` lib).
- Mobile responsive (Tailwind đã handle, verify cơ bản).
- Deploy không crash trên cold start.

## Architecture

```
app/
  ml/
    clustering.py      ← sklearn KMeans wrapper
  routers/
    admin.py           ← /admin/clusters, /admin/seed_demo
    theory.py          ← /theory/{id}
  templates/
    admin_clusters.html
    theory.html
    dashboard.html     ← enhanced
scripts/
  generate_demo_users.py
docs/
  bao-cao.md           ← Markdown báo cáo
  bao-cao.pdf          ← export
  demo-script.md       ← script video
render.yaml
Procfile               ← optional
```

## Related code files

| File | Purpose |
|---|---|
| `app/ml/clustering.py` | KMeans + PCA |
| `app/routers/admin.py` | /admin/clusters + seed_demo |
| `app/routers/theory.py` | Render MD |
| `app/templates/admin_clusters.html` | Scatter chart |
| `app/templates/theory.html` | MD content + nav |
| `app/templates/dashboard.html` | Enhanced (cluster + recommend card) |
| `scripts/generate_demo_users.py` | Demo data |
| `render.yaml` / `Procfile` | Deploy config |
| `docs/bao-cao.md` | Báo cáo |
| `docs/demo-script.md` | Demo script |

## Implementation Steps

### Learning tasks (~3h)

1. **L1:** sklearn KMeans + PCA quickstart (1h).
2. **L2:** Markdown lib Python (`markdown` package) (30m).
3. **L3:** Render.com Python deploy guide (1h).
4. **L4:** OBS Studio basics cho video record (30m).

### Coding tasks (~12h)

**K-means (3h)**
5. **C1:** `clustering.py` — `build_features(users, session)` returns (user_ids, feature_matrix) (1h).
6. **C2:** `cluster_users(features, k=3)` → (labels, centers) (30m).
7. **C3:** `reduce_pca_2d(features)` cho viz (30m).
8. **C4:** Assign cluster name (e.g. 0=yếu, 1=TB, 2=giỏi) bằng order theo avg_mastery của center (30m).
9. **C5:** Endpoint /admin/clusters render scatter Chart.js (45m).

**Demo data (1.5h)**
10. **C6:** `scripts/generate_demo_users.py` — tạo 3 user: alice_weak, bob_avg, carol_strong với pattern attempt khác nhau (1h).
11. **C7:** Endpoint /admin/seed_demo gọi script (30m).

**Theory pages (1.5h)**
12. **C8:** `routers/theory.py` GET /theory/{topic_id} đọc file MD, parse → HTML (45m).
13. **C9:** `theory.html` extend base + render `{{ html|safe }}` + sidebar nav 4 topic (45m).

**Dashboard polish (1.5h)**
14. **C10:** Enhanced `dashboard.html`: cluster card (lấy từ cache hoặc fast compute) (45m).
15. **C11:** Recommend card embed top 3 từ P06 (30m).
16. **C12:** History filter theo topic dropdown + paging (15m, đơn giản query string).

**Deploy (2h)**
17. **C13:** Tạo `render.yaml` hoặc `Procfile` với `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (30m).
18. **C14:** Set env var SESSION_SECRET trên Render dashboard (15m).
19. **C15:** First deploy → debug logs (45m).
20. **C16:** Test full flow trên URL public (30m).

**Báo cáo + demo (2.5h)**
21. **C17:** Outline báo cáo: problem → approach → architecture → algorithms (BKT/IRT/K-means) → results → screenshots (1h).
22. **C18:** Viết báo cáo MD ~8-12 trang (collapse với template trường) (1h).
23. **C19:** Demo script — flow 4 phút: signup → quiz → dashboard → recommend → cluster (30m).
24. **C20:** Record video OBS, edit nhẹ (1h).
25. **C21:** Export PDF + upload (15m).

## Todo list

- [ ] L1: sklearn KMeans
- [ ] L2: markdown lib
- [ ] L3: Render guide
- [ ] L4: OBS basics
- [ ] C1: build_features
- [ ] C2: cluster_users
- [ ] C3: PCA 2D
- [ ] C4: Cluster naming
- [ ] C5: /admin/clusters
- [ ] C6: generate_demo_users
- [ ] C7: /admin/seed_demo
- [ ] C8: /theory/{id}
- [ ] C9: theory.html
- [ ] C10: dashboard cluster card
- [ ] C11: recommend card
- [ ] C12: history filter
- [ ] C13: render.yaml/Procfile
- [ ] C14: env vars
- [ ] C15: First deploy
- [ ] C16: E2E test prod
- [ ] C17: Báo cáo outline
- [ ] C18: Báo cáo body
- [ ] C19: Demo script
- [ ] C20: Record video
- [ ] C21: Export PDF

## Success Criteria

- 3 cluster tách rõ trong scatter plot (visual inspection).
- Demo flow end-to-end chạy trên URL public.
- 4 theory page render OK.
- Báo cáo PDF có:
  - Architecture diagram
  - 3 ML algorithm citations + pseudo-code
  - Screenshots: radar chart, scatter cluster, recommendation
  - So sánh approaches từ BRAINSTORM §6
- Video demo 3-5 phút show: 3 user, 3 mastery khác nhau, 3 recommendation khác nhau, cluster visualization.

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Render cold start >30s | MED | Warm-up ping (UptimeRobot free) trước demo |
| SQLite file mất khi redeploy | HIGH | Cảnh báo trong báo cáo + seed script chạy on startup |
| Cluster không tách (data ít) | MED | Generate demo users với pattern rõ ràng (extreme) |
| Báo cáo viết vội cuối tuần 8 | HIGH | Outline tuần 7, draft incremental |
| Video bị lỗi audio/screen | MED | Test record 30s trước khi record full |
| Pyodide/sklearn install fail Render | LOW | Pin version, check Render Python wheels available |

## Security Considerations

- /admin/* endpoints: bảo vệ bằng admin flag trên User HOẶC hardcoded admin username + check trong dep.
- /admin/seed_demo idempotent — check DB empty trước insert.
- KHÔNG commit `app.db` lên git.
- Session secret PHẢI từ env var trên Render, không hardcode.
- HTTPS auto-enable trên Render (cookie `secure=True`).
- Disable Swagger UI `/docs` trong production (set `docs_url=None` trên FastAPI app).

## Open Questions

- Render free vs Railway — chọn cuối cùng?
- Admin user identification: hardcoded username "admin" hay flag column?
- Báo cáo viết tiếng Việt 100% hay có abstract tiếng Anh?
- Video host: YouTube unlisted, Drive, hay embed trực tiếp?
- Có cần persistence cho SQLite trên Render (tốn $7/month) hay accept reseed?

## Next steps

Submit báo cáo + demo. Future work (nếu môn học sau muốn extend):
- Teacher panel
- Multi-language
- Code execution sandbox
- OAuth
- DKT (Deep Knowledge Tracing — LSTM thay BKT)
