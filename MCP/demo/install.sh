#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
program_dir="$HOME/.local/share/vipi-mcp-demo"
settings_dir="$HOME/.config/vipi-mcp-demo"
unit_dir="$HOME/.config/systemd/user"
mkdir -p "$program_dir" "$settings_dir" "$unit_dir"
chmod 700 "$settings_dir"
cp "$source_dir/server.py" "$source_dir/requirements.txt" "$program_dir/"
if [[ ! -f "$settings_dir/config.json" ]]; then
  cp "$source_dir/config.example.json" "$settings_dir/config.json"
fi
chmod 600 "$settings_dir/config.json"
python3 -m venv "$program_dir/.venv"
"$program_dir/.venv/bin/python" -m pip install -r "$program_dir/requirements.txt"
cp "$source_dir/vipi-mcp-demo.service" "$unit_dir/vipi-mcp-demo.service"
systemctl --user daemon-reload
systemctl --user enable vipi-mcp-demo.service
systemctl --user restart vipi-mcp-demo.service
echo 'MCP mẫu đã khởi động.'
echo "Cấu hình: $settings_dir/config.json"
echo 'Sau khi sửa cấu hình, chạy: systemctl --user restart vipi-mcp-demo.service'
echo 'Địa chỉ mặc định trên cùng máy: ws://127.0.0.1:8765/mcp'
