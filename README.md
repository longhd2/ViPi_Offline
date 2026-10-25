# ViPi — Trợ lý giọng nói tiếng Việt

ViPi kết nối máy chủ với loa ESP32 hoặc Phicomm R1 để trò chuyện, nghe nhạc, radio và điều khiển thiết bị trong nhà.

## Tải và cài đặt

| Thiết bị | Hướng dẫn |
|---|---|
| TV box Linux / Raspberry Pi 64 bit | [Cài ViPi Server ARM64](Server/ARM64/README.md) |
| Tiny / PC Intel, AMD chạy Linux | [Cài ViPi Server AMD64](Server/AMD64/README.md) |
| Loa ESP32-S3 | [Tải firmware và cài ViPi Client](Client/README.md) |
| Loa Phicomm R1 | [Tải APK và cài ViPi R1](R1/README.md) |

## Bắt đầu sử dụng

1. Cài ViPi Server trên máy chủ của bạn.
2. Mở trang quản trị để thiết lập dịch vụ giọng nói và tài khoản API.
3. Cài ứng dụng hoặc firmware phù hợp cho loa, rồi nhập địa chỉ ViPi Server.
4. Đặt tên và chọn giọng đọc riêng cho từng loa trong **Clients**.

## Cập nhật

- **Server:** dùng mục Cập nhật Server trong trang quản trị. [Hướng dẫn bật OTA cho bản Docker đã cài](Server/OTA/README.md).
- **ESP32:** xem hướng dẫn cập nhật trong mục ViPi Client.
- **Phicomm R1:** dùng mục Cập nhật OTA khi đã cấu hình máy hỗ trợ, hoặc cài APK mới theo hướng dẫn R1.

[Tất cả bộ cài và bản cập nhật](https://github.com/longhd2/ViPi_Offline/releases).
