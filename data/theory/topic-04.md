# Chủ đề 4: Lập trình giải bài toán

> Nguồn: SGK Tin học 10 — Cánh Diều, Bài 18 (Chủ đề F). Tóm tắt cho mục đích học tập.

## 1. Bài toán và Thuật toán

- **Bài toán**: vấn đề cần giải quyết với input/output xác định.
- **Thuật toán (algorithm)**: dãy **hữu hạn** các bước rõ ràng để giải bài toán.

### Tính chất của thuật toán

| Tính chất | Ý nghĩa |
|---|---|
| **Tính dừng** (finiteness) | Kết thúc sau số bước hữu hạn |
| **Tính xác định** (definiteness) | Mỗi bước rõ ràng, không mơ hồ |
| **Tính khả thi** (effectiveness) | Mỗi bước thực hiện được |
| **Có Input/Output** | Nhận dữ liệu vào, cho kết quả |

## 2. Các bước giải bài toán bằng máy tính

```
1. Xác định bài toán   (Input gì? Output gì? Ràng buộc?)
2. Tìm thuật toán      (Cách giải)
3. Viết chương trình   (Code Python)
4. Chạy & kiểm thử     (Test với nhiều bộ dữ liệu)
5. Bảo trì             (Sửa lỗi, cải tiến)
```

## 3. Ba cấu trúc điều khiển cơ bản

Mọi thuật toán đều xây dựng từ **3 cấu trúc**:

### 3.1 Tuần tự (Sequence)

Các bước thực hiện **lần lượt** từ trên xuống dưới.

```python
a = int(input("a = "))
b = int(input("b = "))
s = a + b
print("Tổng:", s)
```

### 3.2 Rẽ nhánh (Selection)

**Chọn** thực hiện một trong các nhánh tùy theo điều kiện.

```python
if n % 2 == 0:
    print("n chẵn")
else:
    print("n lẻ")
```

### 3.3 Lặp (Iteration)

**Lặp lại** một khối lệnh nhiều lần.

```python
s = 0
for i in range(1, 101):
    s += i
print(s)  # 5050
```

## 4. Cách biểu diễn thuật toán

### 4.1 Liệt kê các bước (ngôn ngữ tự nhiên)

```
Bài toán: Tìm số lớn nhất trong 3 số a, b, c.
B1. Đặt max = a
B2. Nếu b > max, gán max = b
B3. Nếu c > max, gán max = c
B4. Trả kết quả max
```

### 4.2 Sơ đồ khối (Flowchart)

| Hình | Ý nghĩa |
|---|---|
| ⬭ (oval/bầu dục) | Bắt đầu / Kết thúc |
| ▭ (chữ nhật) | Phép gán, xử lý |
| ◇ (hình thoi) | Điều kiện rẽ nhánh |
| ▱ (hình bình hành) | Nhập / Xuất dữ liệu |
| → (mũi tên) | Hướng đi |

### 4.3 Mã giả (Pseudocode)

Trộn ngôn ngữ tự nhiên + cú pháp lập trình. Không chạy được nhưng diễn đạt rõ ý tưởng.

```
INPUT n
sum ← 0
FOR i ← 1 TO n DO
    sum ← sum + i
OUTPUT sum
```

## 5. Một số thuật toán cơ bản

### 5.1 Tìm max trong dãy

```python
a = [3, 7, 1, 9, 4]
m = a[0]
for x in a[1:]:
    if x > m:
        m = x
print(m)  # 9
```

### 5.2 Tính tổng / trung bình

```python
a = [7, 8, 9, 10, 6]
s = sum(a)
tb = s / len(a)
print(tb)  # 8.0
```

### 5.3 Đếm số chẵn

```python
a = [1, 2, 3, 4, 5, 6]
chan = 0
for x in a:
    if x % 2 == 0:
        chan += 1
print(chan)  # 3
```

### 5.4 Tìm kiếm tuyến tính (linear search)

```python
def tim(a, target):
    for i, x in enumerate(a):
        if x == target:
            return i
    return -1
```

**Độ phức tạp:** trường hợp xấu nhất duyệt qua tất cả n phần tử.

### 5.5 Giải phương trình bậc 2

```python
import math

a = float(input("a = "))
b = float(input("b = "))
c = float(input("c = "))

if a == 0:
    if b == 0:
        print("Vô số nghiệm" if c == 0 else "Vô nghiệm")
    else:
        print("Nghiệm x =", -c/b)
else:
    delta = b*b - 4*a*c
    if delta < 0:
        print("Vô nghiệm thực")
    elif delta == 0:
        print("Nghiệm kép x =", -b/(2*a))
    else:
        r = math.sqrt(delta)
        print(f"x1 = {(-b+r)/(2*a)}, x2 = {(-b-r)/(2*a)}")
```

## 6. Trace (truy vết) thuật toán

Mục đích: kiểm tra giá trị các biến **qua từng bước** để phát hiện lỗi.

### Ví dụ trace

```
s = 0
for i in range(1, 4):
    s = s + i
```

| Bước | i | s |
|---|---|---|
| Khởi tạo | — | 0 |
| Lần 1 | 1 | 1 |
| Lần 2 | 2 | 3 |
| Lần 3 | 3 | 6 |

## 7. Kiểm thử (Testing) — Test case

Thiết kế nhiều **bộ dữ liệu thử** cho cùng 1 chương trình, đặc biệt:

- **Bộ điển hình**: input bình thường (số dương, mảng có vài phần tử).
- **Bộ biên**: input lớn nhất / nhỏ nhất / rỗng.
- **Bộ đặc biệt**: input không hợp lệ, chia cho 0, delta = 0.

Ví dụ test cho phương trình bậc 2:
- `a=1, b=-3, c=2` → 2 nghiệm
- `a=1, b=2, c=1` → nghiệm kép
- `a=1, b=0, c=1` → vô nghiệm
- `a=0, b=2, c=4` → bậc 1
- `a=0, b=0, c=0` → vô số nghiệm

## 8. Lỗi thường gặp

- **Vòng lặp vô hạn**: quên cập nhật biến điều kiện trong `while`.
- **Off-by-one**: dùng `range(1, n)` thay vì `range(1, n+1)`.
- **Sai logic if-else**: thứ tự `elif` quan trọng.
- **Không xử lý edge case**: input rỗng, chia 0.
- **Sai kiểu dữ liệu**: quên `int()` cho input.

## 9. Câu hỏi tự kiểm tra

1. Liệt kê 4 tính chất quan trọng của thuật toán?
2. Khi nào dùng `for`, khi nào dùng `while`?
3. Viết thuật toán tìm số nhỏ nhất trong list `[3, 1, 4, 1, 5, 9]`.
4. Thiết kế ít nhất 4 test case cho thuật toán giải phương trình bậc 2.
5. Trace đoạn:
   ```
   n = 5
   f = 1
   for i in range(1, n+1):
       f = f * i
   ```
   sau khi kết thúc, `f` = ?

## 10. Liên kết với chủ đề khác

- **Chủ đề 3** (Python): công cụ để cài đặt thuật toán.
- **Chủ đề 2** (Dữ liệu): chọn cấu trúc dữ liệu (list, dict) ảnh hưởng độ phức tạp.
