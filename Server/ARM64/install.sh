#!/bin/sh
set -eu
cd "$(dirname "$0")"
[ "$(id -u)" -eq 0 ] || { echo 'Hãy chạy: sudo sh install.sh'; exit 1; }
case "$(uname -m):$(getconf LONG_BIT)" in
  aarch64:64|arm64:64) ;;
  *) echo 'Bộ cài này cần Linux ARM64 và hệ điều hành 64 bit. Hệ điều hành ARM 32 bit hoặc Android không dùng được.'; exit 1;;
esac
sha256sum -c SHA256SUMS
vipi_free_kb=$(df -Pk . | awk 'NR==2 {print $4}')
if [ "$vipi_free_kb" -lt 3145728 ]; then
  echo 'Cần ít nhất 3 GB dung lượng trống trước khi nạp image. Chưa thay đổi server đang chạy.'
  exit 1
fi
if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  command -v apt-get >/dev/null || { echo 'Cần cài Docker Engine và Docker Compose trước.'; exit 1; }
  apt-get update
  if apt-cache show docker-compose-plugin >/dev/null 2>&1; then
    apt-get install -y docker.io docker-compose-plugin
  else
    apt-get install -y docker.io docker-compose
  fi
fi
systemctl enable --now docker
docker load -i vipi-server-arm64.tar.gz
mkdir -p config data cache runtime plugins
if [ ! -f config/secrets.yaml ]; then cp secrets.example.yaml config/secrets.yaml; fi
if [ ! -f .env ]; then
  vipi_lan_ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}')
  if [ -z "$vipi_lan_ip" ]; then vipi_lan_ip=$(hostname -I | awk '{print $1}'); fi
  printf 'VIPI_ADVERTISE_HOST=%s\n' "$vipi_lan_ip" > .env
fi
chown -R 1000:1000 config data cache runtime plugins
chmod 700 config
chmod 600 config/secrets.yaml
docker compose up -d
echo 'ViPi ARM64 đã khởi động. Mở http://IP-MAY:8190 để cấu hình.'
echo 'Tài khoản ban đầu: admin / admin, sau đó đổi mật khẩu.'
