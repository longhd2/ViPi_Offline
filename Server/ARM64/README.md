# Cài ViPi Server Docker ARM64

## Máy phù hợp

- TV box đã chạy Linux Debian/Ubuntu ARM64, chẳng hạn X96 Mini của dự án.
- Raspberry Pi chạy Raspberry Pi OS 64 bit hoặc Debian/Ubuntu ARM64.
- Hệ điều hành phải là 64 bit; CPU 64 bit nhưng cài hệ điều hành 32 bit chưa đủ.
- Bộ cài không chạy trực tiếp trên Android và không chuyển Android thành Linux.
- Nên có RAM từ 2 GB và ít nhất 3 GB dung lượng trống trước khi nạp image.

Trên máy đích, kiểm tra `uname -m` trả về `aarch64` và `getconf LONG_BIT`
trả về `64`. Các Raspberry Pi đời cũ chỉ hỗ trợ ARM 32 bit cần bộ khác.

## Tải bộ cài

[Tải ViPi_Server_Docker_ARM64.zip](https://github.com/longhd2/ViPi_Offline/releases/download/server-arm64-2026.10.16/ViPi_Server_Docker_ARM64.zip) (khoảng 388 MB).

ZIP chứa Docker image đã biên dịch, không cần tải mã nguồn server.
Nếu kho riêng tư, đăng nhập GitHub bằng tài khoản được cấp quyền trước khi tải.

## Cài lần đầu

Chép `ViPi_Server_Docker_ARM64.zip` vào thư mục cá nhân. Mở Terminal hoặc
PuTTY rồi chạy:

```sh
cd ~
sudo apt-get update
sudo apt-get install -y unzip
unzip ViPi_Server_Docker_ARM64.zip
cd ViPi_Server_Docker_ARM64
sudo sh install.sh
```

Script kiểm tra checksum, kiến trúc, dung lượng; cài Docker nếu cần; nạp image
đã biên dịch và bật ViPi. Không tự dừng bản ViPi cũ. Nếu máy đang chạy ViPi
ở các cổng 3103, 8188, 8190 hoặc 8191, cần chủ động dừng bản cũ trước khi
khởi chạy Docker để tránh xung đột. Giữ lại cấu hình cũ khi chuyển đổi.

Xem IP bằng `hostname -I`. Mở `http://IP-MAY:8190`, đăng nhập `admin` / `admin`
rồi đổi mật khẩu ít nhất 12 ký tự. Khai API của bạn trong web quản trị.

Trên ESP32, nhập IP máy ở mục server nội bộ; nếu cần URL đầy đủ, dùng
`ws://IP-MAY:3103/ws`. Docker bridge cần nhập địa chỉ thủ công thay vì chờ
tự tìm server qua multicast.

## Quản lý

Chạy các lệnh trong thư mục `ViPi_Server_Docker_ARM64`:

```sh
sudo docker compose ps
sudo docker compose logs --tail=100 -f
sudo docker compose restart
sudo docker compose down
sudo docker compose up -d
```

`healthy` là trạng thái kiểm tra sức khỏe đã đạt. Ctrl+C chỉ thoát xem log.

Giữ các thư mục config, data, plugins, cache, runtime khi cập nhật. Khóa API
và tài khoản nằm trong `config/secrets.yaml`, không nằm trong image.

Script ghi IP LAN vào file ẩn `.env`. Nếu máy đổi IP, sửa
`VIPI_ADVERTISE_HOST` trong file này, cập nhật IP trên ESP32 rồi chạy:

```sh
sudo docker compose up -d --force-recreate
```
