# Chủ đề 1: Mạng máy tính và Internet

> Nguồn: SGK Tin học 10 — Cánh Diều, Bài 1 (Chủ đề A). Tóm tắt cho mục đích học tập.

## 1. Mạng máy tính là gì?

**Mạng máy tính** là tập hợp các máy tính (và thiết bị) được kết nối với nhau qua đường truyền vật lý (cáp đồng, cáp quang) hoặc không dây (Wi-Fi, sóng radio) để **chia sẻ tài nguyên** và **trao đổi thông tin**.

Lợi ích chính:
- Chia sẻ phần cứng (máy in, ổ cứng).
- Chia sẻ dữ liệu, file.
- Chia sẻ phần mềm, dịch vụ.
- Giao tiếp (email, chat, hội nghị trực tuyến).

## 2. Phân loại mạng theo phạm vi địa lý

| Loại | Phạm vi | Ví dụ |
|---|---|---|
| **PAN** (Personal Area Network) | Vài mét | Bluetooth tai nghe → điện thoại |
| **LAN** (Local Area Network) | Trong tòa nhà / trường học | Mạng phòng máy tính trường |
| **MAN** (Metropolitan Area Network) | Trong một thành phố | Mạng dùng riêng của một thành phố |
| **WAN** (Wide Area Network) | Quốc gia / toàn cầu | Internet |

## 3. Internet và World Wide Web

- **Internet**: hệ thống các mạng máy tính kết nối toàn cầu, dùng chung bộ giao thức **TCP/IP**.
- **World Wide Web (WWW)**: dịch vụ trên Internet, gồm các **trang web** liên kết qua siêu liên kết (hyperlink), truy cập qua giao thức **HTTP/HTTPS**.

**Internet ≠ Web.** Web là một trong nhiều dịch vụ chạy trên Internet (cùng với email, FTP, gọi video, v.v.).

## 4. Các giao thức quan trọng

| Giao thức | Chức năng |
|---|---|
| **HTTP** | Truyền trang web (không mã hóa) |
| **HTTPS** | HTTP có mã hóa SSL/TLS — an toàn |
| **TCP/IP** | Bộ giao thức nền tảng của Internet |
| **DNS** | Chuyển tên miền → địa chỉ IP |
| **SMTP/POP3/IMAP** | Gửi/nhận email |
| **FTP** | Truyền file |

## 5. Địa chỉ IP và Tên miền

- **Địa chỉ IP** (IPv4): dạng `xxx.xxx.xxx.xxx`, mỗi `xxx` từ 0–255. Ví dụ: `192.168.1.1`.
- **Tên miền**: tên dễ nhớ thay cho IP, ví dụ `google.com`.
- **DNS** dịch tên miền sang IP để trình duyệt kết nối được máy chủ.

## 6. URL — Cấu trúc địa chỉ web

```
https://www.example.com:443/path/page.html?id=10
└─┬─┘   └─────┬─────┘ └┬┘ └────┬────┘ └──┬───┘
 giao    tên miền    cổng  đường dẫn  tham số
 thức
```

## 7. Thiết bị mạng cơ bản

- **Modem**: chuyển tín hiệu nhà cung cấp (cáp/quang/4G) → tín hiệu máy tính.
- **Router**: định tuyến gói tin giữa các mạng, cấp IP nội bộ.
- **Switch**: kết nối nhiều thiết bị trong LAN.
- **Access Point**: phát sóng Wi-Fi.

## 8. An toàn khi dùng Internet

- Dùng **HTTPS** khi nhập mật khẩu, thông tin nhạy cảm.
- Cảnh giác với **phishing** (email/web giả mạo).
- Không tải file lạ, không click link không rõ nguồn.
- Dùng mật khẩu mạnh, bật xác thực 2 yếu tố (2FA).
- Cập nhật hệ điều hành + trình duyệt thường xuyên.

## 9. Câu hỏi tự kiểm tra

1. Sự khác biệt giữa Internet và Web?
2. Vì sao trang ngân hàng luôn dùng HTTPS?
3. Khi gõ `youtube.com`, máy tính làm những bước gì để hiển thị trang?
4. Mạng nhà em (Wi-Fi + 3 máy tính) thuộc loại LAN hay WAN?
5. URL `https://vi.wikipedia.org/wiki/Internet` — chỉ ra giao thức, tên miền, đường dẫn?

## 10. Liên kết với chủ đề khác

- **Chủ đề 2** (Dữ liệu): dữ liệu trên mạng được biểu diễn dạng nhị phân, truyền dưới dạng gói tin.
- **Chủ đề 3** (Python): có thể viết chương trình Python để gọi API qua HTTP.
