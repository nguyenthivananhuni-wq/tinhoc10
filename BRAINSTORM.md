# BRAINSTORM — Hệ thống hỗ trợ học Tin học 10 (Cánh Diều)

> Brainstorm session output. Document hóa quyết định kiến trúc + scope. Reference khi code và viết báo cáo.

---

## 1. Problem Statement

Web app cá nhân hóa lộ trình học Tin học 10 Cánh Diều. Mỗi học sinh nhận nội dung khác nhau dựa trên điểm mạnh/yếu thực tế thay vì học cùng trình tự cứng nhắc.

**Đối tượng:** 3 nhóm — mới bắt đầu / trung bình / khá giỏi.

**Mục tiêu báo cáo:** demo concept + **nhấn mạnh yếu tố ML/AI**.

---

## 2. Constraints (quan trọng — định hình mọi quyết định)

| Constraint | Giá trị |
|---|---|
| Loại dự án | Bài tập môn học (demo concept) |
| Team size | 1 người (solo) |
| Timeline | < 2 tháng |
| Trình độ dev | Mới học web, HTML/CSS/JS cơ bản, chưa biết Python |
| Content source | SGK Tin 10 Cánh Diều (tự soạn từ sách) |

---

## 3. Scope Cuts (quyết định cắt — brutal)

| Tính năng spec gốc | Verdict | Lý do |
|---|---|---|
| Đăng nhập Google + Zalo + Email | ❌ → Session-based username/password | OAuth dư thừa cho demo |
| Tài khoản giáo viên theo dõi lớp | ❌ CẮT | Double scope, không cần cho demo concept |
| Video bài giảng 5–10 phút mỗi chủ đề | ❌ CẮT (embed 2-3 YouTube minh họa) | Không tự quay được; production cost cực cao |
| Lý thuyết tóm tắt **toàn bộ** SGK | ⚠️ Chỉ 3–4 chủ đề mẫu | Đủ demo concept, không cần phủ hết |
| Trắc nghiệm | ✅ GIỮ — core feature | Là spine của hệ thống |
| Tự luận có chấm | ❌ CẮT | Auto-grade tự luận = LLM + tốn tiền + sai sót |
| Bài tập Python/Scratch chạy được | ❌ CẮT (nếu muốn → embed Trinket.io iframe) | Code execution sandbox = subsystem riêng |
| Đề ôn thi cuối kỳ | ✅ GIỮ — reuse quiz engine | Chỉ là quiz dài hơn |
| Radar chart mastery | ✅ GIỮ | Visualization key cho báo cáo |
| Huy hiệu + streak ngày học | ❌ CẮT | UI lặp nhiều, giá trị demo thấp |
| ML recommend | ✅ ĐỔI THUẬT TOÁN — xem section 5 | CF không phù hợp cold start |

---

## 4. Architecture — Final

### 4.1 Tech Stack

```
Backend:   Python 3.11 + FastAPI + SQLite + SQLModel
Frontend:  Jinja2 templates + HTMX + Tailwind CSS (CDN) + Chart.js (CDN)
ML:        scikit-learn + numpy (BKT tự code, IRT tự code, K-means dùng sklearn)
Auth:      Session-based (passlib bcrypt + itsdangerous signed cookies)
Deploy:    Render.com hoặc Railway (free tier)
```

### 4.2 Tại sao Python > Node

- **ML libraries native** (numpy/scikit-learn) → không phải tự code math
- **Khớp môn học** — SGK Tin 10 Cánh Diều dạy Python → bonus điểm báo cáo
- **FastAPI beginner-friendly** — auto docs, type hints, ít boilerplate
- Cost học Python: ~1 tuần — chấp nhận được trong 8 tuần

### 4.3 Tại sao HTMX > React/Vue

- Không build tool, không bundler, không npm
- Server-render Jinja2 + attribute HTML (`hx-get`, `hx-post`)
- Học 1 buổi sáng
- Phù hợp dev mới biết JS cơ bản

### 4.4 Database Schema (sơ bộ)

```sql
User (id, username, password_hash, created_at, ability_theta DEFAULT 0.0)
Topic (id, name, order_in_syllabus, parent_id NULL)
Question (id, topic_id, content, difficulty_level [1-3], type [mcq/short], 
          difficulty_b DEFAULT 0.0, options_json, correct_answer)
Attempt (id, user_id, question_id, is_correct, response_time_ms, attempted_at)
MasteryState (user_id, topic_id, p_mastery DEFAULT 0.1, last_updated)
LearningGoal (user_id, goal_type [exam/new_topic/improve/challenge], set_at)
```

---

## 5. ML Strategy (key cho báo cáo)

### Tránh: Collaborative Filtering

**Lý do:** Cold start chết — với <100 user, CF cho output rác. Không defendable.

### Dùng: 3 thuật toán Educational Data Mining chuẩn

#### 5.1 Bayesian Knowledge Tracing (BKT) — CORE
- Tracking P(mastery) theo từng kỹ năng/chủ đề
- 4 tham số: P(L₀) initial knowledge, P(T) learn transition, P(G) guess, P(S) slip
- Sau mỗi response → update P(mastery) bằng Bayes' rule
- **Citation:** Corbett & Anderson (1995). "Knowledge tracing: Modeling the acquisition of procedural knowledge"
- Khan Academy dùng BKT giai đoạn đầu
- Implementation: ~80 dòng Python, hoặc dùng `pyBKT` library

#### 5.2 Item Response Theory (IRT) 1-PL (Rasch model) — ADAPTIVE
- Hiệu chuẩn độ khó câu hỏi `b` từ pattern trả lời
- Formula: `P(correct) = 1 / (1 + exp(-(θ - b)))`
- θ = ability học sinh, b = difficulty câu hỏi
- Dùng để **chọn câu hỏi adaptive** — câu khó vừa phải so với ability hiện tại (target θ ≈ b)
- **Citation:** Rasch (1960). Foundation của TOEFL/GMAT adaptive testing

#### 5.3 K-means Clustering — STUDENT SEGMENTATION
- Cluster học sinh thành 3 nhóm (matching 3 nhóm trong spec)
- Features: avg mastery, avg response time, attempts count, accuracy by difficulty
- sklearn 3 dòng
- Visualization: scatter plot 2D (PCA) cho báo cáo

### 5.4 Recommendation Logic
```
1. Tính mastery vector hiện tại (BKT output mỗi topic)
2. Lấy goal_type của user
3. Apply rule:
   - exam → ưu tiên topic có mastery thấp nhất
   - new_topic → topic tiếp theo trong syllabus mà prerequisite mastery ≥ 0.7
   - improve → topic mastery < 0.5
   - challenge → questions với b cao + topic mastery ≥ 0.8
4. Chọn câu hỏi trong topic đó với b gần θ_user (adaptive)
```

---

## 6. Approaches Evaluated (cho mục báo cáo "so sánh giải pháp")

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| Frontend-only + localStorage | Đơn giản nhất, deploy GitHub Pages | Không multi-device, không ML thật | Loại — user muốn fullstack |
| Node.js + Express fullstack | Một ngôn ngữ (JS) | ML stack yếu, phải tự code math | Loại — báo cáo ML yếu |
| **Python FastAPI + HTMX** | ML native, khớp SGK, simple frontend | Phải học Python | **CHỌN** |
| Django fullstack | Batteries-included, có admin | Overkill, ORM nặng, ít linh hoạt cho ML pipeline | Loại — over-engineered |
| Next.js + Python ML service | Modern, scalable | 2 service = deploy phức tạp, học cong cao | Loại — over scope |

---

## 7. Risks & Mitigation

| Risk | Severity | Mitigation |
|---|---|---|
| **Soạn 120 câu hỏi tốn 2+ tuần** | 🔴 CAO | Fallback: 2 chủ đề × 20 câu = 40 câu đủ demo |
| Học Python + FastAPI chậm hơn 1 tuần | 🟡 TB | Tutorial focused: FastAPI official + W3Schools Python 1 tuần |
| BKT params calibration sai → recommend kém | 🟡 TB | Dùng default params từ paper (P(L₀)=0.1, P(T)=0.2, P(G)=0.2, P(S)=0.1) |
| IRT cần ≥30 responses/câu mới calibrate được | 🟡 TB | Khởi đầu b=0 cho tất cả, recalibrate sau khi có data |
| Deploy lần đầu lỗi | 🟢 THẤP | Render.com có Python template sẵn, dock theo guide |
| Mastery chart không trực quan | 🟢 THẤP | Chart.js radar có sẵn demo |

---

## 8. Success Metrics (cho báo cáo + demo)

**Technical:**
- App chạy được trên Render với URL public
- 4 chủ đề × ≥10 câu hỏi/mức = ≥120 câu (hoặc fallback 40 câu)
- BKT mastery cập nhật real-time sau mỗi quiz
- IRT chọn câu hỏi adaptive đúng nguyên lý (verify bằng test case)
- Radar chart hiển thị ≥4 dimensions
- K-means cluster 3 groups (visualize trong báo cáo)

**Demo flow:**
1. Đăng ký 3 user giả với ability khác nhau (yếu/TB/giỏi)
2. Cho mỗi user làm cùng 1 quiz
3. Show 3 mastery vector khác nhau → 3 recommendation khác nhau
4. Show scatter plot k-means tách rõ 3 cụm

**Báo cáo strength:**
- Trích dẫn 2 papers (Corbett & Anderson 1995, Rasch 1960)
- 3 thuật toán ML thật, không heuristic giả ML
- Architecture diagram rõ ràng
- So sánh approaches có justify

---

## 9. 8-Week Roadmap

| Tuần | Mục tiêu | Deliverable |
|---|---|---|
| 1 | Học Python + FastAPI hello world | App "hello" chạy local + routing cơ bản |
| 2 | Học HTMX + Tailwind + design DB schema | Schema final + migration init |
| 3 | **Soạn ngân hàng câu hỏi** (việc tay chân tốn time nhất) | JSON/seed data ≥120 câu (hoặc fallback 40) |
| 4 | Auth + Quiz flow | User đăng ký, làm quiz, lưu attempt |
| 5 | **Implement BKT** + radar chart | Mastery updated sau mỗi attempt, hiển thị chart |
| 6 | **Implement IRT 1-PL** + recommendation engine | Adaptive question selection chạy đúng |
| 7 | K-means clustering + dashboard + lý thuyết tóm tắt 3-4 bài | Admin view + content page |
| 8 | Deploy + báo cáo + video demo | URL public + báo cáo PDF + video 3-5p |

---

## 10. Next Steps

1. **Setup environment** — Python 3.11, VSCode Python extension, virtualenv
2. **Khởi tạo project structure:**
   ```
   /app
     /routers     (auth.py, quiz.py, dashboard.py)
     /models      (SQLModel definitions)
     /ml          (bkt.py, irt.py, kmeans.py, recommender.py)
     /templates   (Jinja2)
     /static      (css, js)
     main.py
   /data
     questions.json
   /tests
   requirements.txt
   ```
3. **Soạn câu hỏi PARALLEL với coding** — không để dồn vào tuần cuối
4. **Học theo thứ tự:** Python basics → FastAPI → SQLModel → Jinja2 → HTMX → ML (BKT đầu tiên)

---

## 11. Out of Scope (ghi rõ để không drift)

- ❌ Mobile native app
- ❌ Real-time multiplayer / leaderboard
- ❌ Payment / subscription
- ❌ Email notification
- ❌ Multilingual (chỉ tiếng Việt)
- ❌ Teacher dashboard
- ❌ Code execution sandbox
- ❌ Auto-grade tự luận
- ❌ Video hosting (chỉ embed YouTube)
- ❌ OAuth (Google/Zalo)

---

## 12. Decisions Log

| Quyết định | Lý do |
|---|---|
| Python FastAPI (không Node) | ML libraries native + khớp SGK Tin 10 |
| HTMX (không React/Vue) | Không bundler, phù hợp dev mới biết JS |
| SQLite (không Postgres) | Demo concept, không cần multi-writer |
| Session auth (không OAuth) | Tiết kiệm 3-5 ngày, không critical cho demo |
| BKT + IRT + K-means (không CF) | CF cold-start chết với <100 user; BKT/IRT defendable với citations |
| 3-4 chủ đề mẫu (không full SGK) | Demo concept không cần phủ hết content |
| Render.com (không VPS) | Free tier, deploy 5 phút |
