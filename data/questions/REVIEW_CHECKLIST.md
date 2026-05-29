# Review Checklist — Question Bank

> **120 câu hỏi đã được AI draft từ kiến thức CS chuẩn (KHÔNG copy SGK trực tiếp).**
> Bạn PHẢI verify mỗi câu trước khi nộp báo cáo.

## Status

| Topic | File | Số câu | Đã review |
|---|---|---|---|
| 1 — Mạng & Internet | [topic-01-mang-internet.json](./topic-01-mang-internet.json) | 30 | ☐ |
| 2 — Dữ liệu & Thông tin | [topic-02-du-lieu-thong-tin.json](./topic-02-du-lieu-thong-tin.json) | 30 | ☐ |
| 3 — Python cơ bản | [topic-03-python-co-ban.json](./topic-03-python-co-ban.json) | 30 | ☐ |
| 4 — Lập trình giải bài toán | [topic-04-lap-trinh-giai-bai-toan.json](./topic-04-lap-trinh-giai-bai-toan.json) | 30 | ☐ |

## Mỗi câu cần check

- [ ] **Đáp án đúng**: tự giải lại, kiểm tra `correct_answer` thực sự đúng
- [ ] **Wording**: từ ngữ phù hợp lớp 10 không quá khó, không quá dễ
- [ ] **Phù hợp SGK Cánh Diều**: khái niệm có trong SGK không? Nếu không → đổi/xóa
- [ ] **Độ khó đúng level**: dễ (recall) / TB (apply) / khó (analyze)
- [ ] **Không trùng câu**: trong cùng 1 topic không có 2 câu hỏi cùng concept với wording khác nhau
- [ ] **Source page**: đổi `"AI-drafted, verify with SGK"` → tên/số trang SGK thực

## Workflow review (đề xuất)

1. Mở file JSON trong VSCode (có syntax highlight)
2. Đọc từng câu, mark trong giấy: ✅ giữ / 🔄 sửa / ❌ xóa
3. Sửa trực tiếp trong JSON (chú ý syntax — dấu phẩy, dấu ngoặc kép)
4. Sau khi sửa toàn topic: chạy `python -m scripts.import_questions --dry-run` để validate JSON
5. Nếu OK → xóa DB cũ (`Remove-Item data\app.db`) → `python -m app.seed` để re-seed

## Câu nghi ngờ thường gặp (cần check kỹ)

### Topic 1 — Mạng
- Câu IP private range 192.168.x.x — verify SGK có dạy không
- Câu subnet mask /24 → 254 host — toán này có thể quá khó với lớp 10, có thể đổi
- Câu HTTP code 404 — verify SGK có nhắc không

### Topic 2 — Dữ liệu
- Câu chuyển nhị phân ↔ thập phân — kiểm tra phép tính
- Câu tính dung lượng ảnh — verify công thức
- Câu video bitrate 1 Mbps → 75 MB — math: 10×60×1 = 600 Mbit ÷ 8 = 75 MB ✓

### Topic 3 — Python
- Câu list comprehension `[x**2 for x in range(4)]` — có thể quá khó level 3
- Câu slicing `'python'[1:4]` = `'yth'` — verify lại
- Câu swap `a, b = b, a` — concept đúng nhưng SGK có dạy syntax này không?

### Topic 4 — Thuật toán
- Câu FizzBuzz — concept hay nhưng SGK Tin 10 có không?
- Câu Gauss sum formula — verify SGK có dạy không (thường có)
- Câu giai thừa — verify

## Khi sửa câu, giữ schema này

```json
{
  "topic_id": 1,
  "content": "Câu hỏi...",
  "difficulty_level": 1,  // 1=dễ, 2=TB, 3=khó
  "type": "mcq",
  "options": ["A", "B", "C", "D"],  // ĐÚNG 4 options, unique
  "correct_answer": "B",  // PHẢI khớp 1 trong options
  "source_page": "SGK Tin 10 CD, trang 12"  // cập nhật trang thực
}
```

## Validation tự động

```powershell
# Trong PowerShell (venv activated):
python -m scripts.import_questions --dry-run
```

Sẽ báo lỗi nếu:
- Thiếu field bắt buộc
- `options` không phải đúng 4 phần tử
- `options` trùng nhau
- `correct_answer` không có trong `options`
- `difficulty_level` không phải 1/2/3
- JSON syntax sai
