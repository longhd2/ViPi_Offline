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

## ViPi Server 3.0.2

Hỗ trợ nhập lệnh bằng chữ và tìm nhạc trực tiếp trên client ESP32 3.0.1 và R1 0.1.1. Giữ luồng trò chuyện bằng mic, cải thiện trả lời thời tiết và chuyển giữa giọng nói với nhạc.

[Tải ViPi Server 3.0.2](https://github.com/longhd2/ViPi_Offline/releases/tag/server-3.0.2).

## ViPi Server 3.0.1

- Sửa trường hợp loa không đọc câu trả lời khi hỏi giờ hoặc thời tiết.
- Cải thiện luồng trả lời bằng giọng nói.
- Giữ lựa chọn giọng riêng cho từng loa.

[Tải ViPi Server 3.0.1](https://github.com/longhd2/ViPi_Offline/releases/tag/server-3.0.1).

Máy đang dùng phiên bản có tên theo ngày tháng cần làm theo [hướng dẫn chuyển sang 3.0.1](OTA/README.md) một lần. Những lần sau cập nhật trên trang quản trị.

[Hướng dẫn kết nối loa Phicomm R1](../R1/README.md).
