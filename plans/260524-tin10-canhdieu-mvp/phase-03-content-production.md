# Phase 03 — Content Production (Tuần 3, parallel với P04-P06)

## Context links

- Parent: [plan.md](./plan.md)
- Source: [BRAINSTORM.md](../../BRAINSTORM.md) §3 (scope 3-4 chủ đề), §7 (risk soạn câu hỏi cao nhất)
- Reference: [reports/05-content-production-plan.md](./reports/05-content-production-plan.md)
- Depends on: Phase 02 (Question schema chốt → biết field nào cần fill).
- Blocks: seed final của P04 (nhưng không block code).

## Overview

- **Date:** 2026-05-24
- **Description:** Soạn 4 chủ đề × 3 mức độ × 10 câu = 120 câu trắc nghiệm từ SGK Tin 10 Cánh Diều. Lý thuyết tóm tắt 4 chủ đề (Markdown).
- **Priority:** P0 (single biggest risk theo BRAINSTORM)
- **Implementation status:** Not Started
- **Review status:** pending

## Key Insights

- Đây là việc TỐN TIME NHẤT — bắt đầu từ tuần 3 và làm PARALLEL với coding P04-P06, đừng dồn cuối kỳ.
- 120 câu × 5 phút/câu (soạn + verify đáp án) ≈ 10h thuần content work.
- **Fallback hard:** 2 chủ đề × 20 câu = 40 câu nếu trễ trên 1 tuần.
- Đừng tự bịa câu — bám sát SGK để đáp án defendable.
- Format JSON nhất quán → import script đơn giản.
- Mỗi câu cần `difficulty_level` (1=dễ/2=TB/3=khó), `difficulty_b` khởi đầu = 0 (calibrate sau).

## Requirements

### Functional
- 4 file JSON: `data/questions/topic-01.json` ... `topic-04.json`.
- Mỗi file: 30 câu (10 dễ + 10 TB + 10 khó).
- Mỗi câu MCQ: 4 options, 1 correct, content text rõ ràng.
- 4 file Markdown lý thuyết: `data/theory/topic-01.md` ... `topic-04.md` (mỗi file 500-1000 từ).
- Script import `scripts/import_questions.py` đọc JSON → INSERT vào DB.

### Non-functional
- Tiếng Việt chuẩn, không sai chính tả.
- Mỗi câu có `source_page` reference SGK (giúp verify sau).
- License: ghi "Soạn từ SGK Tin 10 Cánh Diều — mục đích học tập".

## Architecture

```
data/
  questions/
    topic-01-mang-internet.json
    topic-02-du-lieu-thong-tin.json
    topic-03-python-co-ban.json
    topic-04-lap-trinh-giai-bai-toan.json
  theory/
    topic-01.md
    topic-02.md
    topic-03.md
    topic-04.md
scripts/
  import_questions.py     ← read JSON → INSERT Question rows
```

## Related code files

| File | Purpose |
|---|---|
| `data/questions/topic-XX.json` (×4) | Question bank |
| `data/theory/topic-XX.md` (×4) | Theory summary |
| `scripts/import_questions.py` | Import script |
| `app/seed.py` | Add `seed_questions()` calling import |

## Implementation Steps

### Content tasks (~12h spread across 3 weeks, ~1.5h/day)

**Topic 1 — Mạng máy tính & Internet (Bài 1 SGK):**
1. **CT1:** Đọc lại SGK bài 1 + ghi note key concepts (45m).
2. **CT2:** Soạn 10 câu dễ (nhận biết: định nghĩa LAN/WAN, ưu điểm mạng, ...) (1.5h).
3. **CT3:** Soạn 10 câu TB (hiểu: phân loại giao thức, IP vs URL) (1.5h).
4. **CT4:** Soạn 10 câu khó (vận dụng: tính số host, scenario thực tế) (2h).
5. **CT5:** Viết theory Markdown topic 1 (1h).

**Topic 2 — Dữ liệu/Thông tin/Xử lý thông tin (Bài 6):** lặp CT1-CT5 (~6h).

**Topic 3 — Python cơ bản (Bài 16):** lặp CT1-CT5 (~6h).

**Topic 4 — Lập trình giải bài toán (Bài 18):** lặp CT1-CT5 (~7h).

### Coding tasks (~3h)

6. **C1:** Define JSON schema template (1 câu mẫu, sẽ copy-paste) (30m).
7. **C2:** Viết `scripts/import_questions.py` — đọc 4 file JSON, validate schema, INSERT vào Question table (1.5h).
8. **C3:** Add `seed_questions()` vào `app/seed.py`, call sau `seed_topics()` (30m).
9. **C4:** Smoke test — chạy import, query DB verify count = 120 (30m).

## Todo list

### Topic 1
- [ ] CT1.1 Read SGK + notes
- [ ] CT1.2 10 câu dễ
- [ ] CT1.3 10 câu TB
- [ ] CT1.4 10 câu khó
- [ ] CT1.5 Theory MD

### Topic 2
- [ ] CT2.1 - CT2.5 (same structure)

### Topic 3
- [ ] CT3.1 - CT3.5

### Topic 4
- [ ] CT4.1 - CT4.5

### Coding
- [ ] C1: JSON schema template
- [ ] C2: import_questions.py
- [ ] C3: seed_questions() hook
- [ ] C4: Verify count = 120

## Success Criteria

- 4 file JSON × 30 câu = 120 câu **HOẶC fallback 2 file × 20 = 40 câu**.
- 4 file theory MD ≥500 từ mỗi file.
- Import script chạy không error, DB có đủ Question.
- Random sample 5 câu mỗi mức → đáp án đúng theo SGK (self-review).

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| **Trễ >1 tuần** | HIGH | Cắt fallback 40 câu (2 chủ đề × 20) ngay khi tuần 4 chưa xong 60 câu |
| Câu hỏi sai đáp án | MED | Self-review pass 2, ưu tiên câu hỏi có sẵn trong SGK + đề luyện |
| Câu mức "khó" thực ra TB | LOW | Đề khó cần kết hợp 2+ concept hoặc tính toán |
| JSON syntax lỗi | LOW | Dùng VSCode JSON validator |
| Trùng câu giữa topic | LOW | Tag source_page rõ |

## Security Considerations

- KHÔNG copy nguyên văn đề bài tập trong SGK (vấn đề bản quyền) — paraphrase + thay số liệu.
- Ghi rõ "soạn cho mục đích học tập, không thương mại".

## Open Questions

- Số câu hỏi mỗi mức có cần cân đối chính xác 10/10/10 hay flex (vd 8/14/8)?
- Có muốn thêm hình ảnh/sơ đồ trong câu hỏi không? (tăng độ phức tạp render)
- Theory MD có cần embed YouTube không? Nếu có → tìm 4 video minh họa.
- Có cần bộ "đề tổng hợp cuối kỳ" riêng (50 câu trộn 4 topic) hay tự gen từ pool?

## Next steps

Phase 04 — Auth + Quiz engine (chạy parallel với content). Khi content xong, P04 đã có data thật để test.
