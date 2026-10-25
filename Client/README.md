# ViPi Client

ViPi Client dành cho ESP32-S3 có Flash 16 MB.

[Tải firmware ViPi Client](https://github.com/longhd2/ViPi_Offline/releases/tag/client-v3.0.0-alpha3.10)

| Tệp | Sử dụng |
|---|---|
| `VIPI_APP.bin` | Cập nhật OTA thiết bị đang dùng ViPi |
| `VIPI_FULL.bin` | Nạp mới/recovery qua USB tại offset 0, gồm gói âm thanh |
| `VIPI_SOUNDS.bin` | Cập nhật riêng âm thanh |
| `manifest.json`, `SHA256SUMS` | Thông tin phiên bản và mã kiểm tra |

Bản này sửa kết nối tên miền, cấu hình Wi-Fi/LED, hiển thị OLED và phản hồi âm lượng. LED thanh chạy theo toàn bộ số bóng đã khai; LED vòng giữ hai vệt ba bóng đối diện. Có lựa chọn tắt LED khi phát nhạc.

Trong web client, khai đúng số LED muốn sử dụng và chọn **Vòng tròn** hoặc **Thanh thẳng**. Các thay đổi LED áp dụng ngay khi lưu nếu không đổi GPIO.

`latest.json`, `manifest.json` và `VERSION` trong thư mục này được dùng để kiểm tra cập nhật Client. Các tệp firmware nằm trong GitHub Release tương ứng.
