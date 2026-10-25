# ViPi R1 cho loa Phicomm R1

Ứng dụng trợ lý giọng nói tiếng Việt cho Phicomm R1 chạy Android 5.1.1. Kết nối tới ViPi Server qua mạng nội bộ hoặc tên miền WSS.

## Tải bộ cài

- [APK ViPi R1 0.1.0-alpha14](https://github.com/longhd2/ViPi_Offline/releases/download/r1-v0.1.0-alpha14/ViPi_R1-0.1.0-alpha14.apk).
- [Mã đối chiếu SHA-256](https://github.com/longhd2/ViPi_Offline/releases/download/r1-v0.1.0-alpha14/SHA256SUMS).
- [Bộ cài ViPi Server](https://github.com/longhd2/ViPi_Offline/blob/main/Server/README.md).

APK là bản Release 

## Chuẩn bị

1. Loa R1 đã kết nối Wi-Fi, ROM cho phép truy cập ADB. Bộ cài này không mở khóa hoặc thay ROM của loa.
2. Máy tính và loa cùng mạng. Tìm địa chỉ IP của loa trong danh sách thiết bị của router.
3. Cài [Android SDK Platform-Tools chính thức của Google](https://developer.android.com/tools/releases/platform-tools). Giải nén, mở cửa sổ lệnh tại thư mục có `adb` và chép APK vừa tải vào thư mục đó.
4. Có ViPi Server đang chạy; ghi lại địa chỉ kết nối và token do server của bạn cấp.

## Cài lần đầu

Ví dụ IP của loa là `192.168.1.48`. Thay địa chỉ này bằng IP loa của bạn. Với PowerShell trên Windows, dùng `./adb.exe` thay cho `adb` trong các lệnh bên dưới.

```sh
adb connect 192.168.1.48:5555
adb -s 192.168.1.48:5555 push ViPi_R1-0.1.0-alpha14.apk /data/local/tmp/ViPi_R1.apk
adb -s 192.168.1.48:5555 shell 'sh -c "pm install -r /data/local/tmp/ViPi_R1.apk"'
```

Chờ kết quả **Success**, rồi mở ứng dụng:

```sh
adb -s 192.168.1.48:5555 shell 'sh -c "am start -n vn.vipi.r1/.MainActivity"'
```

Nếu có ứng dụng trợ lý khác đang giữ micro, hãy dừng ứng dụng đó trước. Nếu Android hỏi quyền micro, cấp quyền cho ViPi R1. Cập nhật tại chỗ bằng `-r` giữ dữ liệu ứng dụng; không gỡ bản cũ trước khi cập nhật.

Nếu gặp `error: closed`, kết nối ADB lại và dùng cách chép APK rồi gọi `sh -c` như trên. Không coi thông báo chép file thành công là đã cài xong: phải có dòng **Success** của trình cài Android. Nếu báo khác chữ ký, dùng APK cùng khóa với bản đang cài; gỡ ứng dụng sẽ làm mất cấu hình và model riêng.

## Mở giao diện và kết nối server

Mở `http://IP-CUA-LOA:8088` bằng trình duyệt trên điện thoại hoặc máy tính cùng mạng. Từ alpha12 không có trang đăng nhập. Trang điều khiển chỉ dành cho LAN; không chuyển tiếp cổng 8088/5555 ra Internet.

Vào **Kết nối → Loa & ViPi Server**:

| Mục | Cách đặt |
|---|---|
| Tên loa | Đặt tên riêng, ví dụ R1 phòng khách |
| Địa chỉ nội bộ | `ws://IP-MAY-CHU:3103/ws` |
| Địa chỉ tên miền | `wss://TEN-MIEN-CUA-BAN/ws` |
| Đường kết nối | Tự động ưu tiên LAN; hoặc chỉ LAN / chỉ tên miền |
| Token server | Nhập token được cấu hình trên server của bạn |

Thay các địa chỉ mặc định bằng server của bạn. Token nhập ở ô riêng, không đưa vào URL. Để ô token trống khi lưu sẽ giữ token đã có. Bấm **Lưu & kết nối lại**, kiểm tra trạng thái **Đã kết nối ViPi** và đường kết nối hiện tại.

Khi dùng tên miền, cấu hình reverse proxy/tunnel trên server để hỗ trợ WebSocket và WSS.

## Sử dụng loa

- **Từ gọi loa:** chọn Porcupine 1.9, bật model Jarvis có sẵn và điều chỉnh độ nhạy. Nói “Jarvis” khi loa đang chờ. Model tùy chỉnh cần đúng Android và đúng SDK; model Raspberry Pi hoặc SDK mới không tương thích.
- **Trò chuyện:** có thể bấm **Bắt đầu nghe** trên Tổng quan. Âm wakeup báo lúc bắt đầu nghe và đến lượt nói tiếp khi bật hội thoại tiếp nối.
- **Âm thanh & LED:** chỉnh âm lượng, mức âm báo, micro, khuếch đại, nguồn thu, LED và chọn giọng riêng cho từng loa. Giọng được lưu theo mã thiết bị trên server hỗ trợ tính năng này. Một số ROM chặn quyền điều khiển LED trực tiếp. Khi giao diện báo lỗi áp dụng LED, cần cấu hình máy hỗ trợ LAN; cài APK không tự cấp thêm quyền hệ thống.
- **Wi-Fi:** bấm Quét Wi-Fi, chờ danh sách mới, chọn hoặc nhập SSID và mật khẩu. Đổi Wi-Fi có thể đổi IP của loa; tìm lại IP trên router để mở trang điều khiển.
- **Bluetooth:** bật/tắt và xem thiết bị đã ghép đôi. Phát âm thanh Bluetooth phụ thuộc dịch vụ Bluetooth gốc của ROM R1.
- **Nút nền:** nếu muốn xử lý nút khi ứng dụng chạy nền, người dùng cần bật Accessibility của ViPi R1 trong Android. Dịch vụ chỉ xử lý phím R1 số 275, không đọc nội dung màn hình. Cài APK không tự cấp quyền này.
- **Nhạc/radio:** yêu cầu bằng giọng nói hoặc dùng Music Center trên ViPi Server. Có nút phát tiếp, tạm dừng, chuyển bài và dừng trong giao diện R1.

## Cập nhật

Nếu đã cấu hình máy hỗ trợ cập nhật LAN: vào **Cập nhật OTA → Kiểm tra cập nhật → Cài bản cập nhật**. Máy hỗ trợ phải đang bật và truy cập được ADB của loa. Hệ thống đối chiếu package, chữ ký và SHA-256. APK công khai không chứa token OTA riêng hoặc khóa ký.

Cài APK lần đầu không tự cấu hình máy hỗ trợ OTA. Khi chưa có máy này, tải APK mới và cài lại theo các lệnh ADB ở trên với `-r`. Không xóa dữ liệu ứng dụng nếu muốn giữ thiết lập và hotword.

## Phạm vi kiểm tra alpha14

Đã thử trên R1 Android 5.1.1: cài qua OTA, giao diện mở trực tiếp, quét Wi-Fi liên tiếp, WSS qua tên miền, chuyển từ LAN lỗi sang tên miền, micro và câu trả lời TTS. Kết nối tên miền đã thử trong cùng mạng nhà; chưa xác nhận trên Wi-Fi/4G của mạng khác. Kiểm tra tệp `BUILD_REPORT.json` đi kèm bản phát hành để biết kết quả riêng của APK Release.
