#!/usr/bin/env python3
"""One-time host service setup, shipped with the Docker installer."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

if os.geteuid() != 0:
    raise SystemExit('Chạy bằng sudo python3 install_ota.py')
root = Path(__file__).resolve().parent
if not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(root)) or not (root / 'compose.yaml').is_file():
    raise SystemExit('Thư mục bộ cài không hợp lệ')
subprocess.run(['openssl', 'version'], check=True, stdout=subprocess.DEVNULL)
tools = Path('/opt/vipi-ota')
conf = Path('/etc/vipi-ota')
tools.mkdir(mode=0o755, exist_ok=True)
conf.mkdir(mode=0o700, exist_ok=True)
key = conf / 'release-public.pem'
incoming = root / 'release-public.pem'
if key.exists() and key.read_bytes() != incoming.read_bytes():
    raise SystemExit('Khóa xác thực phát hành khác bản đã cài; chưa thay đổi dịch vụ')
for name in ['ota_agent.py', 'vipi_update.py']:
    target = tools / name
    tmp = tools / (name + '.new')
    shutil.copyfile(root / name, tmp)
    tmp.chmod(0o755)
    os.replace(tmp, target)
shutil.copyfile(incoming, key)
key.chmod(0o644)
cfg = conf / 'config.json'
cfg.write_text(json.dumps({'root': str(root), 'public_key': str(key)}))
cfg.chmod(0o600)
unit = Path('/etc/systemd/system/vipi-ota.service')
unit.write_text('''[Unit]
Description=ViPi signed server updater
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/vipi-ota/ota_agent.py --config /etc/vipi-ota/config.json
Restart=on-failure
RestartSec=10
UMask=0077
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl', 'daemon-reload'], check=True)
subprocess.run(['systemctl', 'enable', '--now', 'vipi-ota'], check=True)
subprocess.run(['systemctl', 'restart', 'vipi-ota'], check=True)
print('Đã bật cập nhật Server. Mở mục Cập nhật Server trong trang quản trị.')
