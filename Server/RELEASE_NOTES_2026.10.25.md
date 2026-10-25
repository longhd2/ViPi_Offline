ViPi Server 2026.10.25-ota003

- Điều khiển âm lượng qua MCP: đọc, thực hiện, đọc lại mức trên đúng loa; không báo thành công khi chưa xác nhận.
- Home Assistant hỏi rõ thiết bị và xác nhận trạng thái, tránh báo đã bật khi không có thiết bị phù hợp.
- Sửa nhận diện câu mở radio và hỗ trợ luồng VOV3 đã cập nhật.
- Chọn giọng riêng cho từng ESP32 hoặc R1; cải thiện trang Clients và thông tin kết nối.
- Bộ cài AMD64 và ARM64 chứa ứng dụng biên dịch Cython; không chứa mã nguồn ứng dụng, API key hoặc cấu hình đang dùng.
- Có gói OTA ký Ed25519, SHA-256 và bộ cài Docker mới. Đã kiểm tra nâng cấp từ ota001, giữ cấu hình/dữ liệu và khôi phục bản cũ.
- 268 kiểm thử nguồn, 7 kiểm tra an toàn OTA, smoke test hai kiến trúc và rà toàn bộ layer image đã đạt. ARM64 được chạy dưới giả lập trên Tiny; chưa cài bộ Docker mới trên Raspberry Pi thật.

Xem README trong bộ cài hoặc hướng dẫn Server trong kho ViPi_Offline.
