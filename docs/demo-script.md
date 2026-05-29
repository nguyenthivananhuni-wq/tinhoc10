# Kịch bản demo video (3–5 phút)

> Mục tiêu: cho thấy 3 thuật toán ML (BKT, IRT, K-means) chạy thật + cá nhân hóa.

## Chuẩn bị trước khi quay

1. Chạy server: `uvicorn app.main:app --reload`
2. Tạo dữ liệu demo: đăng nhập tài khoản admin → `/admin/seed_demo`
   (hoặc `python -m scripts.generate_demo_users`).
   → có sẵn `alice_weak`, `bob_avg`, `carol_strong` (mật khẩu `demo123456`).
3. Mở sẵn các tab: `/`, `/login`, `/recommend`, `/dashboard`, `/admin/clusters`.

## Phân cảnh

| Thời lượng | Nội dung | Điểm nhấn |
|---|---|---|
| 0:00–0:30 | Giới thiệu bài toán + kiến trúc | "Cá nhân hóa lộ trình học bằng 3 thuật toán ML" |
| 0:30–1:30 | Đăng nhập học sinh mới → làm 1 quiz 10 câu | Mỗi câu hiện đáp án ngay; nói về **BKT cập nhật mastery** |
| 1:30–2:15 | Mở `/dashboard` | **Radar chart** mastery 4 chủ đề + nhóm học tập |
| 2:15–3:00 | Mở `/recommend`, đổi mục tiêu ở `/goal` | Gợi ý **đổi theo mục tiêu**; nhắc **IRT chọn câu theo θ** |
| 3:00–4:00 | Đăng nhập admin → `/admin/clusters` | **Scatter PCA**: 3 học sinh tách 3 cụm yếu/TB/giỏi |
| 4:00–4:30 | Tổng kết | 3 thuật toán + 3 citation + định hướng mở rộng |

## Câu chốt

> "Cùng một bộ câu hỏi, ba học sinh khác năng lực nhận được ba lộ trình khác
> nhau — đó là cá nhân hóa bằng BKT, IRT và K-means."
