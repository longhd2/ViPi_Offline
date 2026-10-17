# Bật cập nhật Server cho bản ViPi Docker đã cài

[Tải bộ bật OTA](https://github.com/longhd2/ViPi_Offline/releases/download/server-2026.10.17-ota001/ViPi_Server_OTA_Enable.zip).

Chỉ cần thực hiện một lần. Giữ nguyên thư mục đang cài ViPi, không xóa cấu hình và không cài lại hệ điều hành hoặc Docker.

1. Chép ViPi_Server_OTA_Enable.zip vào máy chủ và giải nén.
2. Mở Terminal/PuTTY, vào thư mục ViPi_Server_OTA_Enable.
3. Chọn lệnh phù hợp bên dưới. Thay đường dẫn nếu bạn cài ViPi ở thư mục khác.

Raspberry Pi / TV box Linux ARM64:

```sh
sudo python3 enable_ota.py --root "$HOME/ViPi_Server_Docker_ARM64"
```

Tiny / PC AMD64:

```sh
sudo python3 enable_ota.py --root "$HOME/ViPi_Server_Docker_AMD64"
```

Chờ thông báo hoàn tất, sau đó mở http://IP-MAY:8190/update và đăng nhập tài khoản quản trị đang dùng.

Từ lần sau, chọn Kiểm tra bản mới rồi Cập nhật ngay trên web. Server tạm ngắt kết nối khi chuyển phiên bản. Cấu hình, tài khoản và khóa API được giữ lại; nếu bản mới lỗi hệ thống tự khôi phục bản trước.

Nút Khôi phục bản trước dùng để quay lại phiên bản và dữ liệu tại thời điểm trước cập nhật. Hãy cập nhật khi thiết bị không trò chuyện hoặc phát nhạc. Giữ thư mục .vipi-ota để còn khả năng khôi phục.
