# ViPi Server

## Cài trực tiếp trên máy chủ

Chạy trong terminal hoặc phiên SSH của máy Linux:

```sh
sudo apt-get update
sudo apt-get install -y git python3 ca-certificates
git clone https://github.com/longhd2/ViPi_Offline.git
cd ViPi_Offline
bash install.sh
```

Script tự nhận máy Intel/AMD hoặc ARM64. Bộ cài được đặt trong thư mục `ViPi_Server_Docker_AMD64` hoặc `ViPi_Server_Docker_ARM64` ở thư mục cá nhân.

Máy đã có ViPi nên cập nhật từ trang quản trị để giữ cấu hình.

- [Đã cài Docker: bật cập nhật OTA](OTA/README.md).
- [Cài mới trên TV box / Raspberry Pi 64 bit](ARM64/README.md).
- [Cài mới trên Tiny / PC Intel, AMD](AMD64/README.md).

Hướng dẫn có các bước lấy khóa Groq API và kết nối ESP32.

## Bản 2026.10.25-ota003

Bổ sung xác nhận MCP/âm lượng và Home Assistant, sửa điều khiển radio và chọn giọng riêng cho từng loa trong **Clients**. Các bản cài AMD64/ARM64 và gói OTA đã ký nằm trong [bản phát hành server](https://github.com/longhd2/ViPi_Offline/releases/tag/server-2026.10.25-ota003).

[Hướng dẫn kết nối loa Phicomm R1](../R1/README.md). Mỗi người cài tự nhập khóa API, thiết bị Home Assistant và danh sách đài của mình.
