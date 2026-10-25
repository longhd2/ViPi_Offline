# MCP mẫu cho ViPi

Mẫu này dùng kết nối WebSocket của ViPi Server, có ba công cụ. Cần Linux với Python 3.10 trở lên.

| Câu nói sau khi gọi loa | Chức năng |
|---|---|
| “Xem giờ mẫu” | Đọc giờ hiện tại |
| “Cộng mẫu 7 với 5” | Cộng hai số |
| “Bật đèn mẫu”, “tắt đèn mẫu”, “xem đèn mẫu” | Thay đổi hoặc xem một đèn mô phỏng |

Đèn mẫu không phải thiết bị thật và trở về tắt khi dịch vụ MCP khởi động lại. Phép cộng nhận chữ số hoặc các số từ không đến mười viết bằng tiếng Việt.

## 1. Cài MCP trên Tiny hoặc máy Linux

```sh
sudo apt-get update
sudo apt-get install -y git python3 python3-venv ca-certificates
git clone https://github.com/longhd2/ViPi_Offline.git
cd ViPi_Offline
bash MCP/demo/install.sh
```

Nếu đã có kho ViPi_Offline, vào thư mục đó chạy `git pull`, rồi chạy lệnh cài MCP ở dòng cuối.

Cấu hình riêng được lưu tại `~/.config/vipi-mcp-demo/config.json`. Cài lại mẫu này giữ cấu hình đã có.

## 2. ViPi Server và MCP trên cùng máy

Trước khi lưu MCP, xem địa chỉ Server trên giao diện loa và mở đúng trang quản trị của Server đó.

Giữ cấu hình MCP mặc định, rồi mở mục **MCP** trong trang quản trị ViPi Server:

- Bật MCP.
- Địa chỉ: `ws://127.0.0.1:8765/mcp`.
- Công cụ cho phép: `demo.time`, `demo.add`, `demo.light`.
- Lưu và chờ trạng thái đã kết nối.

[Mẫu cấu hình ViPi Server](vipi-config.example.json) có các trường để tham khảo. Chỉ thêm hoặc sửa mục `mcp`; giữ nguyên các phần cấu hình khác của bạn. Nếu dùng Docker, làm theo mục bên dưới thay cho địa chỉ loopback.

## 3. ViPi Server và MCP trên hai máy trong LAN

Trong cấu hình MCP, đổi `listen` thành địa chỉ LAN của máy chạy MCP và cho phép IP máy chạy Server. Ví dụ minh họa:

```json
{
  "listen": "192.168.1.20",
  "port": 8765,
  "allowed_clients": ["127.0.0.1/32", "192.168.1.10/32"],
  "timezone": "Asia/Ho_Chi_Minh"
}
```

Thay `.20` bằng IP máy MCP, `.10` bằng IP máy Server. Trên ViPi Server nhập `ws://192.168.1.20:8765/mcp` theo IP thực tế, rồi khởi động lại MCP:

```sh
systemctl --user restart vipi-mcp-demo.service
```

Danh sách `allowed_clients` là các máy được phép kết nối trực tiếp. Đặt IP cố định trên router để cấu hình không thay đổi sau khi khởi động lại.

## 4. ViPi Server chạy bằng Docker

`127.0.0.1` trong container là chính container. Hãy dùng địa chỉ mà container truy cập được đến máy MCP và thêm địa chỉ nguồn tương ứng vào `allowed_clients`.

- MCP trên một máy Tiny khác: dùng IP LAN của Tiny, cho phép IP LAN của máy chủ Docker.
- MCP cùng máy chủ Docker: MCP cần lắng nghe ở địa chỉ host mà container truy cập được; danh sách cho phép cần có mạng bridge thực tế của container.

Xem địa chỉ container và cổng về host:

```sh
sudo docker inspect vipi-server --format '{{range .NetworkSettings.Networks}}IP Server: {{.IPAddress}} | Gateway: {{.Gateway}}{{end}}'
```

Khi MCP cùng máy chủ Docker, đặt `listen` của MCP thành `0.0.0.0`, thêm IP Server vừa hiện vào `allowed_clients` với đuôi `/32`, và trên ViPi nhập `ws://GATEWAY:8765/mcp` theo giá trị Gateway. Khởi động lại MCP sau khi lưu. Chỉ cho phép IP hoặc mạng thực sự dùng cho kết nối này.

## 5. Bắt đầu sử dụng

Khi ViPi báo đã kết nối và có ba công cụ, gọi loa rồi nói một câu trong bảng ở đầu trang. Câu trả lời về đèn luôn ghi rõ đó là đèn mô phỏng.

| Việc cần làm | Lệnh |
|---|---|
| Xem trạng thái | `systemctl --user status vipi-mcp-demo.service` |
| Xem thông tin hoạt động | `journalctl --user -u vipi-mcp-demo.service -n 30 --no-pager` |
| Khởi động lại | `systemctl --user restart vipi-mcp-demo.service` |
| Dừng | `systemctl --user stop vipi-mcp-demo.service` |
| Tắt tự khởi động | `systemctl --user disable --now vipi-mcp-demo.service` |

Muốn chạy dịch vụ ngay sau khi máy khởi động, kể cả chưa đăng nhập: chạy `sudo loginctl enable-linger "$USER"`.

Mẫu này dành cho LAN hoặc cùng máy. Đường `/health` dùng để xem dịch vụ có sẵn sàng; các công cụ nằm ở `/mcp`.
