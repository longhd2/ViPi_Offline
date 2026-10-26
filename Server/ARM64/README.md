# Cài đặt ViPi Server trên TV box và Raspberry Pi

## 1. Chuẩn bị

- TV box chạy Linux Debian/Ubuntu ARM64 hoặc Raspberry Pi chạy Raspberry Pi OS 64 bit.
- RAM từ 2 GB, dung lượng trống ít nhất 3 GB và kết nối Internet.
- Máy tính có trình duyệt và PuTTY để đăng nhập máy cài ViPi.

Bộ cài dành cho Linux 64 bit. Kiểm tra trên máy bằng hai lệnh:

```sh
uname -m
getconf LONG_BIT
```

Kết quả cần là `aarch64` và `64`. Nếu TV box đang chạy Android, cần cài Linux phù hợp với thiết bị trước.

## 2. Cài trực tiếp bằng Git

Đăng nhập SSH vào máy Linux sẽ cài ViPi, hoặc mở terminal ngay trên máy, rồi chạy:

```sh
sudo apt-get update
sudo apt-get install -y git python3 ca-certificates
git clone https://github.com/longhd2/ViPi_Offline.git
cd ViPi_Offline
bash install.sh
```

Script tự tải và giải nén bộ cài phù hợp. Khi được yêu cầu, nhập mật khẩu sudo của tài khoản trên máy chủ.

Bộ cài được đặt tại `~/ViPi_Server_Docker_ARM64`. Sau khi cài hoàn tất, tiếp tục thiết lập ở bước dưới.

Nếu đã có bản ViPi đang chạy, xem [hướng dẫn cập nhật](../OTA/README.md). Script cài mới không ghi đè thư mục đã có dữ liệu.

## 3. Mở trang quản trị

Xem IP của máy:

```sh
hostname -I
```

Trên trình duyệt của máy tính hoặc điện thoại cùng mạng, mở `http://IP-MAY:8190`. Thay `IP-MAY` bằng IP vừa tìm được.

Lần cài mới, đăng nhập bằng tên `admin`, mật khẩu `admin`, rồi đổi sang mật khẩu mới có ít nhất 12 ký tự. Nếu dùng lại cấu hình cũ, đăng nhập bằng tài khoản đã có.

## 4. Lấy khóa Groq API

1. Mở [trang tạo khóa Groq](https://console.groq.com/keys), đăng ký hoặc đăng nhập tài khoản.
2. Chọn **Create API Key**.
3. Đặt tên dễ nhớ, ví dụ `ViPi`, rồi xác nhận tạo khóa.
4. Sao chép khóa vừa tạo để nhập vào ViPi.

Khóa cần lấy ở **GroqCloud**. Giữ riêng khóa của bạn, không gửi vào nhóm chat hay đưa lên GitHub. Hạn mức sử dụng được quản lý trong tài khoản Groq.

## 5. Khai báo API vào ViPi

Trong trang quản trị ViPi, mở phần **Tài khoản & API**:

1. Dán khóa vào ô **Groq API Key mới**, rồi bấm **Lưu khóa Groq**. Chỉ dán nội dung khóa, không thêm dấu nháy hoặc chữ `Bearer`.
2. Bấm **Kiểm tra khóa đã lưu**. Khi báo **Xác thực Groq thành công**, khóa đã dùng được.
3. Ở ô **Model trò chuyện**, nhập `openai/gpt-oss-120b`.
4. Đánh dấu **Bật LLM** và **Cho LLM gọi công cụ nhạc**, rồi bấm **Lưu LLM**.
5. Ở **Dịch vụ nhận giọng nói**, có thể giữ **Google**; nếu chọn **Groq**, bấm **Lưu dịch vụ**.

Ô nhập khóa được xóa sau khi lưu để giữ kín khóa; xem trạng thái **Đã cấu hình** và dùng nút kiểm tra để xác nhận.

Nếu ViPi vẫn dùng cấu hình trước đó, khởi động lại trong thư mục bộ cài:

```sh
sudo docker compose restart
```

Tài liệu chính thức: [Lấy khóa và bắt đầu dùng Groq](https://console.groq.com/docs/quickstart), [các model đang hỗ trợ](https://console.groq.com/docs/models).

## 6. Kết nối ESP32

Mở web cấu hình của ESP32, nhập vào mục server nội bộ:

```text
ws://IP-MAY:3103/ws
```

Thay `IP-MAY` bằng IP máy cài ViPi. ESP32 và máy chủ cần cùng mạng để kết nối qua địa chỉ này. Lưu cấu hình, sau đó thử gọi wake word và hỏi giờ.

Nếu sử dụng tên miền, nhập thêm địa chỉ WebSocket do bạn đã thiết lập, dạng `wss://TEN-MIEN/ws`, và chọn ưu tiên LAN. Tên miền cần được cấu hình chuyển tiếp tới máy chủ trước khi sử dụng.

## 7. Sử dụng và bảo trì

Chạy các lệnh sau trong thư mục `ViPi_Server_Docker_ARM64`:

| Việc cần làm | Lệnh |
| --- | --- |
| Xem trạng thái | `sudo docker compose ps` |
| Khởi động lại | `sudo docker compose restart` |
| Dừng ViPi | `sudo docker compose down` |
| Bật ViPi | `sudo docker compose up -d` |
| Xem log gần nhất | `sudo docker compose logs --tail=50` |

Giữ lại các thư mục `config`, `data`, `plugins`, `cache`, `runtime` khi cập nhật. Cấu hình và khóa API được lưu trong `config/secrets.yaml`.

Nên đặt IP cố định cho máy chủ trên router. Nếu IP thay đổi, cập nhật địa chỉ trên ESP32 và giá trị `VIPI_ADVERTISE_HOST` trong tệp `.env` của bộ cài, rồi chạy:

```sh
sudo docker compose up -d --force-recreate
```

## 8. Khi gặp lỗi

| Hiện tượng | Cách kiểm tra |
| --- | --- |
| Không mở được trang quản trị | Kiểm tra đúng IP, cùng mạng và trạng thái bằng `sudo docker compose ps`. |
| Báo cổng đã được sử dụng | Kiểm tra và dừng bản ViPi cũ đang dùng cổng 3103, 8188, 8190 hoặc 8191. |
| Khóa Groq không hợp lệ | Sao chép lại đúng khóa từ GroqCloud, lưu rồi bấm kiểm tra; tạo khóa mới nếu khóa cũ đã bị thu hồi. |
| Groq báo hết hạn mức | Kiểm tra hạn mức trong GroqCloud và thử lại sau thời gian được thông báo. |
| Model không khả dụng | Kiểm tra tên model trong danh sách Groq đang hỗ trợ và quyền sử dụng của tài khoản. |
| ESP32 chưa kết nối | Kiểm tra URL có dạng `ws://IP-MAY:3103/ws` và ESP32 đang ở cùng mạng. |


## Cập nhật Server qua web

Nếu đã cài bản Docker cũ, [bật OTA một lần theo hướng dẫn này](../OTA/README.md), giữ nguyên cấu hình hiện tại. Bộ cài mới đã bật sẵn dịch vụ cập nhật.

Mở **Cập nhật Server** trong trang quản trị, chọn **Kiểm tra bản mới** rồi **Cập nhật**. Không cần cài lại Docker hay khai lại API. ViPi tạm ngắt kết nối lúc chuyển phiên bản. Nếu bản mới lỗi, hệ thống tự khôi phục bản trước. Nút **Khôi phục bản trước** khôi phục cả phiên bản và dữ liệu trước cập nhật. Hãy cập nhật khi thiết bị không trò chuyện hoặc phát nhạc.
