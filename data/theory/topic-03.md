# Chủ đề 3: Python cơ bản

> Nguồn: SGK Tin học 10 — Cánh Diều, Bài 16 (Chủ đề F). Tóm tắt cho mục đích học tập.

## 1. Python là gì?

**Python** là ngôn ngữ lập trình **bậc cao**, **thông dịch** (interpreted), cú pháp gần với ngôn ngữ tự nhiên, dùng phổ biến trong giáo dục, khoa học dữ liệu, web, AI.

Đặc điểm:
- Cú pháp ngắn gọn, dễ đọc.
- **Thụt lề bắt buộc** (xác định khối lệnh).
- Phân biệt **chữ hoa/thường** (`Name` ≠ `name`).
- Không cần khai báo kiểu trước (dynamic typing).

## 2. Biến và kiểu dữ liệu cơ bản

```python
ten = "Anh"      # str   — chuỗi
tuoi = 16        # int   — số nguyên
chieu_cao = 1.65 # float — số thực
da_di_hoc = True # bool  — True/False
```

| Kiểu | Mô tả | Ví dụ |
|---|---|---|
| `int` | Số nguyên | 10, -3, 0 |
| `float` | Số thực | 3.14, 0.5 |
| `str` | Chuỗi ký tự | "hello", 'a' |
| `bool` | Logic | True, False |
| `list` | Danh sách (mutable) | [1, 2, 3] |
| `tuple` | Bộ (immutable) | (1, 2, 3) |
| `dict` | Từ điển key→value | {"a": 1} |

## 3. Nhập / xuất

```python
ten = input("Nhập tên: ")   # đọc chuỗi từ bàn phím
n = int(input("Nhập n: "))  # đọc rồi chuyển sang int
print("Xin chào", ten)
print(f"n = {n}, n² = {n**2}")  # f-string format
```

## 4. Các toán tử

| Loại | Toán tử |
|---|---|
| Số học | `+ - * / // % **` |
| So sánh | `== != < <= > >=` |
| Logic | `and or not` |
| Gán | `= += -= *= /=` |

Ví dụ phép chia:
- `7 / 2` = `3.5` (chia thực)
- `7 // 2` = `3` (chia nguyên — bỏ phần thập phân)
- `7 % 2` = `1` (lấy phần dư)
- `2 ** 10` = `1024` (lũy thừa)

## 5. Cấu trúc rẽ nhánh

```python
diem = int(input("Nhập điểm: "))
if diem >= 8:
    print("Giỏi")
elif diem >= 6.5:
    print("Khá")
elif diem >= 5:
    print("Trung bình")
else:
    print("Yếu")
```

## 6. Cấu trúc lặp

### for — lặp với số lần biết trước

```python
for i in range(5):        # i = 0, 1, 2, 3, 4
    print(i)

for i in range(1, 11):    # i = 1..10
    print(i)

for i in range(2, 11, 2): # i = 2, 4, 6, 8, 10 (bước 2)
    print(i)
```

### while — lặp khi điều kiện đúng

```python
n = 0
while n < 5:
    print(n)
    n += 1
```

### break, continue

- `break` — thoát ngay khỏi vòng lặp.
- `continue` — bỏ qua phần còn lại, sang vòng kế.

## 7. Danh sách (list)

```python
diem = [7, 8, 9, 10, 6]

print(diem[0])      # 7  — chỉ số bắt đầu từ 0
print(diem[-1])     # 6  — phần tử cuối
print(diem[1:4])    # [8, 9, 10]  — slicing
print(len(diem))    # 5
print(sum(diem))    # 40
print(max(diem))    # 10
print(min(diem))    # 6

diem.append(5)      # thêm cuối
diem.sort()         # sắp xếp tăng dần
```

## 8. Chuỗi (string)

```python
s = "Python"
print(len(s))       # 6
print(s[0])         # 'P'
print(s[-1])        # 'n'
print(s[1:4])       # 'yth'
print(s.upper())    # 'PYTHON'
print(s.lower())    # 'python'
print("py" in s.lower())  # True
```

## 9. Hàm

```python
def chao(ten, loi="Xin chào"):
    return f"{loi}, {ten}!"

print(chao("Anh"))                # Xin chào, Anh!
print(chao("Bình", "Hello"))      # Hello, Bình!
```

- `def` định nghĩa hàm.
- Tham số có thể có **giá trị mặc định**.
- `return` trả kết quả.

## 10. Ví dụ tổng hợp — Tính BMI

```python
ten = input("Tên: ")
chieu_cao = float(input("Chiều cao (m): "))
can_nang = float(input("Cân nặng (kg): "))

bmi = can_nang / (chieu_cao ** 2)
print(f"{ten}, BMI = {bmi:.2f}")

if bmi < 18.5:
    print("Thiếu cân")
elif bmi < 23:
    print("Bình thường")
elif bmi < 25:
    print("Thừa cân")
else:
    print("Béo phì")
```

## 11. Câu hỏi tự kiểm tra

1. Viết chương trình nhập n và in tổng 1 + 2 + ... + n.
2. Kết quả của `5 + 3 * 2` là gì? `(5 + 3) * 2`?
3. Khác biệt giữa `print(2 + 2)` và `print("2 + 2")`?
4. Cho `a = [1, 2, 3, 4, 5]`. Output của `a[::-1]`?
5. Khi nào dùng `for` và khi nào dùng `while`?

## 12. Liên kết với chủ đề khác

- **Chủ đề 4** (Lập trình giải bài toán): dùng Python để cài đặt thuật toán.
- **Chủ đề 2** (Dữ liệu): kiểu dữ liệu Python phản ánh cách máy tính biểu diễn dữ liệu.
