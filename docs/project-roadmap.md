# Project Roadmap — Hệ thống học Tin học 10 (Cánh Diều)

> Cập nhật: 2026-05-29 · App version 0.7.0 · 156 tests pass

## Trạng thái tổng thể

| Mảng | Trạng thái |
|---|---|
| Backend (FastAPI + SQLModel + SQLite) | ✅ Hoàn thành |
| 3 thuật toán ML (BKT · IRT · K-means) | ✅ Hoàn thành + unit test |
| Quiz engine (HTMX, adaptive) | ✅ Hoàn thành |
| UI redesign (theme tím + sidebar) | ✅ Hoàn thành |
| Panel giáo viên (admin) | ✅ Hoàn thành |
| Deploy thật (Render) · video · PDF báo cáo | ⏳ Thủ công, chưa làm |

## Đã hoàn thành (7 phase + mở rộng)

### P01–P04 — Nền tảng
- FastAPI app, SQLite + SQLModel (User, Topic, Question, Attempt, MasteryState, LearningGoal).
- Auth session-cookie (bcrypt + itsdangerous), register/login/logout.
- Ngân hàng câu hỏi MCQ + import script.
- Quiz engine HTMX: 10 câu/session, hiện đáp án ngay.

### P05 — BKT mastery
- `app/ml/bkt.py` (Corbett & Anderson 1995), cập nhật mastery mỗi câu.
- Radar chart mastery 4 chủ đề trên `/dashboard`.

### P06 — IRT + Recommendation
- `app/ml/irt.py` (Rasch 1-PL, MLE θ), chọn câu adaptive `|b−θ|` min.
- `app/ml/recommender.py` — 4 nhánh goal (exam/improve/new_topic/challenge).
- `/recommend` + script hiệu chuẩn độ khó `calibrate_difficulty.py`.

### P07 — K-means + dashboard + deploy config
- `app/ml/clustering.py` — KMeans(k=3) + PCA 2D, gom nhóm Yếu/TB/Giỏi.
- `/admin/clusters` scatter plot + `generate_demo_users.py`.
- Deploy config: `render.yaml`, `Procfile`, hardening (ẩn /docs prod, cookie Secure).

### P08 — UI redesign + Panel giáo viên (ngoài plan gốc, 2026-05-29)
- **Redesign toàn bộ UI**: theme tím/lavender, font Poppins, layout sidebar cho app + nav cho trang công khai. Hệ thống template: `base.html` → `base_app.html` / `base_public.html`.
- **Panel giáo viên** (admin, gated `require_admin`):
  - `/admin/overview` — thống kê toàn lớp (phân bố điểm, câu khó/dễ nhất, chủ đề yếu nhất).
  - `/admin/students` + `/admin/students/{id}` — danh sách + chi tiết từng học sinh.
  - `/admin/questions` (GET+POST) — xem/thêm câu hỏi.
- **`/profile`** — trang hồ sơ cá nhân.
- **UX/bảo mật**: 401 → redirect `/login` (thay vì JSON), fix N+1 query clustering, fix FK cascade khi `--force` seed, strip `correct_answer`.

## Còn lại (thủ công — cần tài khoản/thiết bị của người dùng)

| Việc | Ghi chú |
|---|---|
| Deploy lên Render.com | Config sẵn (`render.yaml`); cần kết nối GitHub + tài khoản Render |
| Quay video demo 3–5 phút | Kịch bản sẵn: [docs/demo-script.md](./demo-script.md) |
| Export báo cáo ra PDF | Nội dung sẵn: [docs/bao-cao.md](./bao-cao.md) |

## Hướng phát triển tương lai (nếu mở rộng)
- Cache kết quả clustering (TTL) hoặc tính nền — hiện chạy mỗi lần load dashboard.
- Sửa/xóa câu hỏi trong panel admin (hiện chỉ thêm).
- Forget-curve cho mastery; θ per-topic thay vì global.
- Deep Knowledge Tracing (LSTM) thay BKT.
