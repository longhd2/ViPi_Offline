#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null 2>&1 || {
  echo 'Cần Python 3. Chạy: sudo apt-get install -y python3 ca-certificates' >&2
  exit 1
}
exec python3 "$root/tools/install_server.py" "$@"
