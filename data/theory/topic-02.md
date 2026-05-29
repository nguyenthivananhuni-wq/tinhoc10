# Chủ đề 2: Dữ liệu, thông tin và xử lý thông tin

> Nguồn: SGK Tin học 10 — Cánh Diều, Bài 6 (Chủ đề C). Tóm tắt cho mục đích học tập.

## 1. Dữ liệu và thông tin

- **Dữ liệu (data)**: các sự kiện, con số, ký hiệu thô **chưa được xử lý**. Ví dụ: `38.5`, `"Hà Nội"`, `1010`.
- **Thông tin (information)**: dữ liệu **đã qua xử lý** và có ý nghĩa với người nhận. Ví dụ: `"Nhiệt độ Hà Nội 38.5°C → trời nóng"`.

**Mối quan hệ:** Dữ liệu → (Xử lý) → Thông tin → (Quyết định/Hành động).

## 2. Biểu diễn dữ liệu trong máy tính

Máy tính **chỉ làm việc với hai trạng thái**: bật/tắt (1/0). Do đó mọi dữ liệu đều được mã hóa thành **dãy bit** (binary digits).

- **Bit**: đơn vị nhỏ nhất, có giá trị **0** hoặc **1**.
- **Byte**: 8 bit. Biểu diễn được 2⁸ = **256** giá trị.

### Đơn vị đo dung lượng (quy ước nhị phân thường dùng)

| Đơn vị | Bằng |
|---|---|
| 1 byte (B) | 8 bit |
| 1 KB | 1024 B |
| 1 MB | 1024 KB |
| 1 GB | 1024 MB |
| 1 TB | 1024 GB |

## 3. Hệ đếm

| Hệ | Cơ số | Chữ số dùng | Ví dụ |
|---|---|---|---|
| Thập phân | 10 | 0–9 | 25 |
| Nhị phân | 2 | 0, 1 | 11001 |
| Bát phân | 8 | 0–7 | 31 |
| Thập lục phân | 16 | 0–9, A–F | 19, FF |

### Chuyển đổi nhị phân ↔ thập phân

**Nhị phân → thập phân:** mỗi chữ số nhân với 2 mũ vị trí (từ phải sang).
```
1010₂ = 1·2³ + 0·2² + 1·2¹ + 0·2⁰ = 8 + 0 + 2 + 0 = 10₁₀
```

**Thập phân → nhị phân:** chia liên tiếp cho 2, ghi phần dư từ dưới lên.
```
5 ÷ 2 = 2 dư 1
2 ÷ 2 = 1 dư 0
1 ÷ 2 = 0 dư 1     → 5₁₀ = 101₂
```

## 4. Mã hóa ký tự

- **ASCII** (7-8 bit): mã hóa 128/256 ký tự — chữ Latin, số, dấu câu. `'A'` = 65, `'a'` = 97, `'0'` = 48.
- **Unicode** (UTF-8/16/32): mã hóa được hầu hết ký tự của mọi ngôn ngữ — kể cả tiếng Việt có dấu, chữ Hán, emoji.

## 5. Phân loại dữ liệu trong tin học

### Theo kiểu

| Kiểu | Ví dụ |
|---|---|
| Số (numeric) | 10, 3.14 |
| Văn bản (text) | "Xin chào" |
| Hình ảnh (image) | .jpg, .png |
| Âm thanh (audio) | .mp3, .wav |
| Video | .mp4, .avi |
| Logic (boolean) | True/False |

### Theo cấu trúc

- **Có cấu trúc**: bảng tính, CSDL quan hệ (hàng/cột rõ).
- **Phi cấu trúc**: văn bản tự do, ảnh, video, bài đăng mạng xã hội.

## 6. Quy trình xử lý thông tin

```
Thu thập → Lưu trữ → Xử lý → Truyền → Trình bày
```

1. **Thu thập** dữ liệu (cảm biến, bàn phím, file).
2. **Lưu trữ** (RAM, ổ cứng, đám mây).
3. **Xử lý** (CPU thực hiện phép toán/logic).
4. **Truyền** (mạng, USB).
5. **Trình bày** (màn hình, máy in, loa).

## 7. Nén dữ liệu (Compression)

Mục đích: **giảm dung lượng** lưu trữ và truyền tải.

- **Nén không mất (lossless)**: zip, rar, png, flac — khôi phục **100%** dữ liệu gốc.
- **Nén có mất (lossy)**: jpg, mp3, mp4 — bỏ bớt chi tiết khó nhận biết → kích thước nhỏ hơn nhiều.

## 8. Tính toán dung lượng — ví dụ

**Văn bản 5000 ký tự ASCII:** 5000 × 1 byte = 5000 B ≈ **5 KB**.

**Ảnh trắng đen 100×100 pixel, 1 bit/pixel:** 100 × 100 = 10 000 bit = 10 000 ÷ 8 = **1250 byte**.

**Video 10 phút bitrate 1 Mbps:** 10 × 60 × 1 Mbit = 600 Mbit ÷ 8 = **75 MB**.

## 9. Câu hỏi tự kiểm tra

1. Phân biệt dữ liệu và thông tin? Cho ví dụ.
2. Vì sao máy tính dùng hệ nhị phân?
3. Chuyển 13₁₀ sang nhị phân?
4. Mã ASCII của `'D'` là bao nhiêu (biết `'A'` = 65)?
5. Khi nào nên dùng nén có mất, khi nào không?

## 10. Liên kết với chủ đề khác

- **Chủ đề 1** (Mạng): dữ liệu trên mạng truyền dạng gói tin nhị phân.
- **Chủ đề 3** (Python): các kiểu `int`, `str`, `float` tương ứng cách biểu diễn dữ liệu.
