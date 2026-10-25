# ViPi Server

- [Đã cài Docker: bật cập nhật OTA](OTA/README.md).
- [Cài mới trên TV box / Raspberry Pi 64 bit](ARM64/README.md).
- [Cài mới trên Tiny / PC Intel, AMD](AMD64/README.md).

Hướng dẫn có các bước lấy khóa Groq API và kết nối ESP32.

## Bản 2026.10.25-ota003

Bổ sung xác nhận MCP/âm lượng và Home Assistant, sửa điều khiển radio và chọn giọng riêng cho từng loa trong **Clients**. Các bản cài AMD64/ARM64 và gói OTA đã ký nằm trong [bản phát hành server](https://github.com/longhd2/ViPi_Offline/releases/tag/server-2026.10.25-ota003).

Ứng dụng được biên dịch thành module Cython; gói công khai không kèm nguồn Python của ứng dụng hay cấu hình đang dùng. Mã máy vẫn có thể được phân tích, không phải mã hóa chống dịch ngược tuyệt đối.

Đã qua 268 kiểm thử nguồn, 7 kiểm tra an toàn OTA, smoke test hai kiến trúc và thử nâng cấp/khôi phục có giữ dữ liệu. ARM64 chạy dưới giả lập trong lần kiểm tra bộ cài này.

[Hướng dẫn kết nối loa Phicomm R1](../R1/README.md). Mỗi người cài tự nhập khóa API, thiết bị Home Assistant và danh sách đài của mình.
