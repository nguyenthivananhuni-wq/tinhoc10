# Report 05 — Content Production Plan

> Reference cho Phase 03. 120 câu hỏi + 4 theory MD.

## 4 chủ đề chốt (từ SGK Tin 10 Cánh Diều)

| # | Bài SGK | Tên chủ đề | Topic.name |
|---|---|---|---|
| 1 | Bài 1 (Chủ đề A) | Mạng máy tính & Internet | Mạng máy tính và Internet |
| 2 | Bài 6 (Chủ đề C) | Dữ liệu - thông tin - xử lý thông tin | Dữ liệu, thông tin và xử lý thông tin |
| 3 | Bài 16 (Chủ đề F) | Ngôn ngữ lập trình & Python cơ bản | Python cơ bản |
| 4 | Bài 18 (Chủ đề F) | Lập trình giải bài toán | Lập trình giải bài toán |

## Phân bổ câu hỏi

| Topic | Dễ (1) | TB (2) | Khó (3) | Total |
|---|---|---|---|---|
| 1 — Mạng & Internet | 10 | 10 | 10 | 30 |
| 2 — Dữ liệu/Thông tin | 10 | 10 | 10 | 30 |
| 3 — Python cơ bản | 10 | 10 | 10 | 30 |
| 4 — Lập trình giải bài toán | 10 | 10 | 10 | 30 |
| **Total** | **40** | **40** | **40** | **120** |

**Fallback (nếu trễ):** chỉ làm topic 1+3 × 20 câu = 40 câu (đủ demo).

## Mức độ — định nghĩa

| Level | Bloom | Đặc điểm |
|---|---|---|
| 1 — Dễ | Remember/Understand | Nhận biết khái niệm, định nghĩa, từ khóa SGK |
| 2 — TB | Apply | Áp dụng quy tắc, tính toán đơn giản, phân loại |
| 3 — Khó | Analyze/Evaluate | Scenario thực tế, kết hợp 2+ concept, gen output Python |

## JSON Schema (1 câu mẫu)

```json
{
  "topic_id": 1,
  "content": "Giao thức nào sau đây dùng để truyền trang web trên Internet?",
  "difficulty_level": 1,
  "type": "mcq",
  "difficulty_b": 0.0,
  "options": ["FTP", "HTTP", "SMTP", "POP3"],
  "correct_answer": "HTTP",
  "source_page": "SGK Tin 10 CD, trang 12"
}
```

File format = array of objects:
```json
[
  { "topic_id": 1, "content": "...", ... },
  { "topic_id": 1, "content": "...", ... }
]
```

## File structure

```
data/
  questions/
    topic-01-mang-internet.json           ← 30 câu
    topic-02-du-lieu-thong-tin.json       ← 30 câu
    topic-03-python-co-ban.json           ← 30 câu
    topic-04-lap-trinh-giai-bai-toan.json ← 30 câu
  theory/
    topic-01.md
    topic-02.md
    topic-03.md
    topic-04.md
```

## Theory MD template

```markdown
# Mạng máy tính và Internet

## 1. Giới thiệu
[2-3 đoạn intro]

## 2. Khái niệm cốt lõi
- **LAN**: ...
- **WAN**: ...
- **Internet**: ...

## 3. Các giao thức quan trọng
- HTTP/HTTPS
- TCP/IP
- DNS

## 4. Ví dụ minh họa
[1-2 ví dụ]

## 5. Câu hỏi tự kiểm tra
[3-5 câu reflection]

> Nguồn: SGK Tin 10 Cánh Diều, bài 1
```

Yêu cầu: 500-1000 từ/file.

## Workflow soạn câu hỏi (per topic, ~6h)

```
1. (45m) Đọc SGK bài tương ứng + ghi note key concepts vào file scratch
2. (1.5h) Soạn 10 câu DỄ — bám sát definition trong SGK
3. (1.5h) Soạn 10 câu TB — câu áp dụng, ví dụ có sẵn trong SGK
4. (2h)   Soạn 10 câu KHÓ — câu phân tích, kết hợp khái niệm, sinh output Python
5. (1h)   Viết theory MD cho topic
```

## Sample questions per topic

### Topic 1 — Mạng & Internet

**Dễ:** "URL là viết tắt của?"  
A. Universal Resource Link  
B. **Uniform Resource Locator** ✓  
C. Unified Resource Location  
D. User Resource Locator

**TB:** "Địa chỉ IP 192.168.1.1 thuộc loại gì?"  
A. **Địa chỉ riêng (private)** ✓  
B. Địa chỉ công cộng (public)  
C. Địa chỉ loopback  
D. Địa chỉ multicast

**Khó:** "Mạng LAN có 254 host khả dụng. Subnet mask phù hợp?"  
A. 255.255.255.0  
B. **255.255.255.0 (/24)** ✓  
C. 255.255.0.0  
D. 255.0.0.0

### Topic 3 — Python cơ bản

**Khó:** "Output của đoạn code: `print([x**2 for x in range(4) if x % 2 == 0])`?"  
A. `[0, 1, 4, 9]`  
B. **`[0, 4]`** ✓  
C. `[0, 2]`  
D. Error

## Anti-pattern (tránh)

- KHÔNG copy nguyên văn đề bài SGK (bản quyền) — paraphrase + thay số/scenario.
- KHÔNG để 2 option đúng cùng lúc.
- KHÔNG dùng "tất cả các đáp án trên" làm correct (lười).
- KHÔNG câu lừa kiểu chỉ khác dấu phẩy nhỏ.
- KHÔNG câu khó vì lượng từ dài thay vì khái niệm sâu.

## Import workflow

```bash
python -m scripts.import_questions data/questions/
# → Validate JSON schema mỗi file
# → INSERT vào Question table
# → Print "Imported 120 questions across 4 topics"
```

## Quality check

- Random 5 câu/mức → tự làm lại sau 1 ngày, đáp án đúng → pass.
- Distribution kiểm tra: với 30 câu, không quá 8 câu cùng 1 mục con (tránh overfit narrow concept).

## Unresolved questions

- 10/10/10 exact mỗi mức hay flex (8/14/8)?
- Câu có hình ảnh/sơ đồ — có cần không (tăng render complexity)?
- Theory MD có embed YouTube minh họa không?
- Có cần bộ "đề tổng hợp 50 câu cuối kỳ" riêng hay tự gen từ pool?
- Hỗ trợ short answer (tự luận ngắn) hay chỉ MCQ 4 đáp án?
