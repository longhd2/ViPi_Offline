# Cập nhật ViPi Server

## Bản đang dùng tên phiên bản theo ngày tháng

Để chuyển sang ViPi Server 3.0.1, thực hiện một lần trên máy đang cài Server. Cấu hình và tài khoản hiện tại được giữ lại.

Nếu đã có thư mục ViPi_Offline, vào thư mục đó và chạy `git pull`. Nếu chưa có, chạy:

```sh
git clone https://github.com/longhd2/ViPi_Offline.git
cd ViPi_Offline
```

TV box / Raspberry Pi Linux ARM64:

```sh
sudo python3 Server/OTA/enable_ota.py --root "$HOME/ViPi_Server_Docker_ARM64"
```

Tiny / PC Intel, AMD:

```sh
sudo python3 Server/OTA/enable_ota.py --root "$HOME/ViPi_Server_Docker_AMD64"
```

Thay đường dẫn nếu thư mục ViPi nằm ở nơi khác. Chờ thông báo hoàn tất rồi mở `http://IP-MAY:8190/update`.

Có thể [tải bộ hỗ trợ cập nhật](https://github.com/longhd2/ViPi_Offline/releases/download/server-3.0.1/ViPi_Server_OTA_Enable.zip), giải nén và chạy cùng lệnh trên với `enable_ota.py` trong thư mục vừa giải nén.

## Từ phiên bản 3.0.1 trở đi

Đăng nhập trang quản trị, mở **Cập nhật Server**, chọn **Kiểm tra bản mới** rồi **Cập nhật**.

Hãy cập nhật khi loa đang nghỉ. Server tạm ngắt kết nối trong lúc cập nhật và các loa sẽ kết nối lại sau đó. Nếu cập nhật không thành công, hệ thống quay về bản trước.

**Khôi phục bản trước** đưa cả phiên bản và dữ liệu về thời điểm trước cập nhật. Giữ thư mục `.vipi-ota` để dùng tính năng này.
