#!/usr/bin/env python3
"""Enable signed OTA on an existing ViPi Docker installation once."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True, type=Path)
args = parser.parse_args()
if os.geteuid() != 0:
    raise SystemExit('Chạy bằng sudo python3 enable_ota.py --root THU-MUC-VIPI')
source = Path(__file__).resolve().parent
root = args.root.resolve()
if not (root / 'compose.yaml').is_file():
    raise SystemExit('Không tìm thấy compose.yaml trong thư mục đã chọn')
subprocess.run(['openssl', 'version'], check=True, stdout=subprocess.DEVNULL)
key = Path('/etc/vipi-ota/release-public.pem')
if key.exists() and key.read_bytes() != (source / 'release-public.pem').read_bytes():
    raise SystemExit('Khóa phát hành khác bản đã cài; chưa thay đổi server')
for name in ['ota_agent.py', 'vipi_update.py', 'install_ota.py', 'release-public.pem']:
    target = root / name
    if target.resolve() != (source / name).resolve():
        shutil.copyfile(source / name, target)
    target.chmod(0o644 if name.endswith('.pem') else 0o755)
sys.path.insert(0, str(root))
from ota_agent import Agent
was_active = subprocess.run(['systemctl', 'is-active', '--quiet', 'vipi-ota']).returncode == 0
if was_active:
    subprocess.run(['systemctl', 'stop', 'vipi-ota'], check=True)
try:
    agent = Agent({'root': str(root), 'public_key': str(root / 'release-public.pem')})
    with (agent.state / 'agent.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        agent.recover_interrupted()
        agent.apply()
    subprocess.run([sys.executable, str(root / 'install_ota.py')], check=True)
except Exception:
    if was_active:
        subprocess.run(['systemctl', 'start', 'vipi-ota'])
    print('Chưa bật được OTA. Bản ViPi hiện tại được giữ lại hoặc khôi phục. Kiểm tra mạng, dung lượng và thử lại.', file=sys.stderr)
    raise SystemExit(1)
print('Hoàn tất. Từ nay mở /update trong trang quản trị để cập nhật ViPi.')
