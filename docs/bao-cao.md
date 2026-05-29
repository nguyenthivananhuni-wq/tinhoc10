# Báo cáo: Hệ thống hỗ trợ học Tin học 10 (Cánh Diều) cá nhân hóa bằng ML

> Môn học: Tin học 10 · Bộ sách Cánh Diều
> Sinh viên thực hiện: _(điền tên)_
> Ngày: _(điền ngày nộp)_

---

## 1. Đặt vấn đề

Học sinh lớp 10 học Tin học với cùng một lộ trình cố định, không phân biệt năng
lực và điểm yếu của từng người. Hệ thống này cá nhân hóa việc học: mỗi học sinh
làm quiz trắc nghiệm, hệ thống **theo dõi mức độ thành thạo (mastery)** theo từng
chủ đề, **chọn câu hỏi phù hợp với năng lực**, **gợi ý chủ đề nên học tiếp**, và
**phân nhóm học sinh** để giáo viên nắm tổng quan lớp học.

## 2. Mục tiêu

- Theo dõi mastery theo từng chủ đề sau mỗi câu trả lời (real-time).
- Chọn câu hỏi adaptive theo năng lực — không quá dễ, không quá khó.
- Gợi ý lộ trình học theo mục tiêu cá nhân (ôn thi / học mới / cải thiện / thách thức).
- Phân nhóm học sinh (yếu / trung bình / giỏi) cho góc nhìn lớp học.

## 3. Kiến trúc hệ thống

**Stack:** Python 3.11 · FastAPI · SQLite + SQLModel · Jinja2 + HTMX · Tailwind
CDN · Chart.js CDN · scikit-learn + numpy.

```
Browser (HTMX + Tailwind + Chart.js)
        │  HTTP
        ▼
FastAPI (app/main.py)
   ├── routers/   auth, pages (+ /profile), quiz, dashboard, recommend, admin (panel GV)
   ├── ml/        bkt.py (BKT) · irt.py (IRT) · recommender.py · clustering.py
   ├── models/    SQLModel: User(+is_admin), Topic, Question, Attempt, MasteryState, LearningGoal
   ├── templates/ base → base_app (sidebar) / base_public (nav) — theme tím
   └── db.py      SQLite (data/app.db)
```

Luồng dữ liệu chính:

```
Trả lời câu hỏi → lưu Attempt
   → BKT cập nhật MasteryState (mastery theo topic)
   → kết thúc session: IRT ước lượng ability θ
Bắt đầu quiz → IRT chọn câu có độ khó b ≈ θ
Dashboard / Recommend → BKT mastery + goal + IRT
Admin → K-means gom nhóm học sinh
```

## 4. Thuật toán Machine Learning

### 4.1 Bayesian Knowledge Tracing (BKT) — theo dõi mastery

Mô hình 4 tham số (Corbett & Anderson, 1995): P(L₀)=0.1, P(T)=0.2, P(G)=0.2,
P(S)=0.1. Sau mỗi câu, cập nhật xác suất học sinh đã nắm chủ đề bằng Bayes:

```
# Bước 1 — posterior theo quan sát
if đúng:   P(L|obs) = P(L)(1-S) / [ P(L)(1-S) + (1-P(L))G ]
if sai:    P(L|obs) = P(L)·S   / [ P(L)·S   + (1-P(L))(1-G) ]
# Bước 2 — chuyển trạng thái học
P(L_mới) = P(L|obs) + (1 - P(L|obs))·T
```

Code: [app/ml/bkt.py](../app/ml/bkt.py). Kiểm chứng: 16 unit test
([tests/test_bkt.py](../tests/test_bkt.py)). Trực quan hóa: **radar chart** mastery
4 chủ đề trên trang `/dashboard`.

### 4.2 Item Response Theory 1-PL / Rasch — chọn câu adaptive

Xác suất trả lời đúng: `P(correct) = 1 / (1 + exp(-(θ - b)))` với θ = năng lực
học sinh, b = độ khó câu hỏi (Rasch, 1960). Năng lực θ ước lượng bằng **MLE
(gradient ascent)** trên log-likelihood; gradient = Σ(yᵢ − pᵢ).

- **Chọn câu adaptive:** trong chủ đề đã chọn, lấy câu có `|b − θ|` nhỏ nhất →
  tối đa thông tin Fisher (Rasch: cực đại tại b = θ).
- **Hiệu chuẩn độ khó b:** script offline [scripts/calibrate_difficulty.py](../scripts/calibrate_difficulty.py)
  suy `b ≈ -logit(p)` từ tỷ lệ trả lời đúng (cần ≥10 lượt/câu).

Code: [app/ml/irt.py](../app/ml/irt.py), [app/ml/recommender.py](../app/ml/recommender.py).
Kiểm chứng: [tests/test_irt.py](../tests/test_irt.py), [tests/test_recommender.py](../tests/test_recommender.py).

### 4.3 K-means — phân nhóm học sinh

Gom học sinh thành **K=3 nhóm** (yếu/trung bình/giỏi) trên 4 đặc trưng:
`avg_mastery`, `avg_response_time_ms`, `total_attempts`, `accuracy_hard`. Pipeline:
StandardScaler → KMeans(k=3) → đặt tên nhóm theo mastery trung bình của tâm cụm.
Trực quan: **scatter plot PCA 2D** tại `/admin/clusters` (MacQueen, 1967).

Code: [app/ml/clustering.py](../app/ml/clustering.py). Kiểm chứng:
[tests/test_clustering.py](../tests/test_clustering.py).

### 4.4 Logic gợi ý (recommendation)

| Mục tiêu | Quy tắc chọn chủ đề |
|---|---|
| Ôn thi (exam) | Ưu tiên chủ đề mastery thấp nhất |
| Cải thiện (improve) | Chủ đề mastery < 0.5 |
| Học mới (new_topic) | Chủ đề kế tiếp trong syllabus mà chủ đề trước đã ≥ 0.7 |
| Thách thức (challenge) | Chủ đề mastery ≥ 0.8, làm câu khó |

Sau khi chọn chủ đề → IRT chọn câu có b gần θ. Hiển thị tại `/recommend`.

## 5. Kết quả

- **Đầy đủ test tự động:** 156 test pass (`pytest`).
- **BKT:** 5 câu đúng liên tiếp → mastery chủ đề ≥ 0.9 (đúng kỳ vọng paper).
- **IRT:** học sinh giỏi vs yếu → θ khác nhau rõ; câu hỏi tiếp theo bám sát θ.
- **K-means:** 3 học sinh demo (alice_weak / bob_avg / carol_strong) tách thành
  3 cụm rõ trên scatter plot.
- **Giao diện:** UI theme tím + sidebar, responsive (Tailwind), font Poppins.
- **Panel giáo viên (admin):** thống kê toàn lớp, danh sách + chi tiết học sinh,
  thêm câu hỏi — bảo vệ bằng phân quyền `require_admin`.

### Ảnh chụp màn hình (chèn khi nộp)

1. Radar chart mastery — `/dashboard`
2. Trang gợi ý — `/recommend`
3. Scatter cluster PCA — `/admin/clusters`

## 6. So sánh các giải pháp đã cân nhắc

| Phương án | Ưu | Nhược | Kết luận |
|---|---|---|---|
| Frontend-only + localStorage | Đơn giản, deploy dễ | Không ML thật, không đa thiết bị | Loại |
| Node.js + Express | Một ngôn ngữ JS | Stack ML yếu | Loại |
| **Python FastAPI + HTMX** | ML native, đơn giản frontend | Phải học Python | **Chọn** |
| Django | Có sẵn admin | Nặng, ORM cồng kềnh | Loại |

(Chi tiết: [BRAINSTORM.md](../BRAINSTORM.md) §6.)

## 7. Hạn chế & hướng phát triển

- SQLite trên Render free tier mất dữ liệu khi container restart (cần persistent
  disk trả phí hoặc reseed) → đã thêm seed lại khi khởi động.
- BKT/IRT dùng tham số mặc định từ paper, chưa hiệu chuẩn trên dữ liệu thật quy mô lớn.
- Hướng mở rộng: panel cho giáo viên, Deep Knowledge Tracing (LSTM) thay BKT,
  sandbox chạy code Python.

## 8. Tài liệu tham khảo

1. Corbett, A. T., & Anderson, J. R. (1995). *Knowledge tracing: Modeling the
   acquisition of procedural knowledge.* User Modeling and User-Adapted Interaction.
2. Rasch, G. (1960). *Probabilistic Models for Some Intelligence and Attainment Tests.*
3. MacQueen, J. (1967). *Some methods for classification and analysis of
   multivariate observations.* Berkeley Symposium.
