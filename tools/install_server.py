"""Fetch the matching public installer and prepare a fresh installation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE = 2 * 1024**3
MAX_EXPANDED = 8 * 1024**3


class InstallError(Exception):
    pass


def architecture(machine=None):
    machine = (machine or platform.machine()).lower()
    if machine in ("x86_64", "amd64"):
        return "AMD64"
    if machine in ("aarch64", "arm64"):
        return "ARM64"
    raise InstallError("Bộ cài hỗ trợ Linux AMD64 hoặc ARM64, không hỗ trợ hệ điều hành 32 bit.")


def metadata(root, arch):
    data = json.loads((root / "Server" / arch / "latest.json").read_text(encoding="utf-8"))
    url = urlsplit(data.get("url", ""))
    expected = "ViPi_Server_Docker_" + arch + ".zip"
    valid_url = (
        url.scheme == "https" and url.hostname == "github.com"
        and url.username is None and url.password is None and url.port is None
        and not url.query and not url.fragment
        and re.fullmatch(r"/longhd2/ViPi_Offline/releases/download/server-[A-Za-z0-9.-]+/" + re.escape(expected), url.path)
    )
    size = data.get("size")
    if (not valid_url or type(size) is not int or not 0 < size <= MAX_ARCHIVE
            or not re.fullmatch(r"[0-9a-f]{64}", data.get("sha256", ""))
            or data.get("platform") != "linux/" + arch.lower()):
        raise InstallError("Thông tin bộ cài chưa hợp lệ. Hãy chạy git pull rồi thử lại.")
    return data


def valid_archive(path, info):
    if not path.is_file() or path.is_symlink() or path.stat().st_size != info["size"]:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest() == info["sha256"]


class HttpsRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https":
            raise InstallError("Đường tải bộ cài không hợp lệ.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(info, cache):
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = cache / (info["sha256"] + ".zip")
    if valid_archive(destination, info):
        print("Đã có bộ cài, đang chuẩn bị…", flush=True)
        return destination
    print("Đang tải bộ cài ViPi Server…", flush=True)
    fd, name = tempfile.mkstemp(prefix="download-", suffix=".part", dir=cache)
    partial = Path(name)
    try:
        request = Request(info["url"], headers={"User-Agent": "ViPi-Installer", "Accept-Encoding": "identity"})
        received, last_percent = 0, -1
        with os.fdopen(fd, "wb") as output, build_opener(HttpsRedirects()).open(request, timeout=60) as response:
            if response.status != 200:
                raise InstallError("Chưa tải được bộ cài. Hãy thử lại.")
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                received += len(block)
                if received > info["size"]:
                    raise InstallError("Tệp tải về không khớp bộ cài. Hãy thử lại.")
                output.write(block)
                percent = received * 100 // info["size"]
                if percent // 10 != last_percent // 10:
                    print("Đã tải " + str(percent) + "%", flush=True)
                    last_percent = percent
        if not valid_archive(partial, info):
            raise InstallError("Tệp tải về chưa đầy đủ hoặc không khớp bộ cài. Hãy thử lại.")
        os.replace(partial, destination)
        return destination
    finally:
        partial.unlink(missing_ok=True)


def ensure_fresh(target):
    if target.is_symlink() or (target.exists() and (not target.is_dir() or any(target.iterdir()))):
        raise InstallError("Thư mục đã có dữ liệu: " + str(target) + ". Hãy dùng mục cập nhật trên web hoặc chọn thư mục cài mới.")


def unpack(archive, target, arch):
    ensure_fresh(target)
    parent_name = "ViPi_Server_Docker_" + arch
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle, tempfile.TemporaryDirectory(prefix=".vipi-install-", dir=target.parent) as work:
        entries, seen, total = [], set(), 0
        for member in bundle.infolist():
            rel = PurePosixPath(member.filename)
            mode = member.external_attr >> 16
            if (rel.is_absolute() or ".." in rel.parts or "\\" in member.filename
                    or not rel.parts or rel.parts[0] != parent_name
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or member.filename in seen):
                raise InstallError("Nội dung bộ cài không hợp lệ.")
            seen.add(member.filename)
            total += member.file_size
            if total > MAX_EXPANDED:
                raise InstallError("Bộ cài vượt dung lượng cho phép.")
            entries.append((member, Path(work).joinpath(*rel.parts)))
        stage = Path(work) / parent_name
        for member, output in entries:
            if member.is_dir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as source, output.open("xb") as destination:
                    shutil.copyfileobj(source, destination)
                output.chmod(0o755 if output.suffix == ".sh" else 0o644)
        if not (stage / "install.sh").is_file() or not (stage / "compose.yaml").is_file():
            raise InstallError("Bộ cài thiếu tệp cần thiết.")
        ensure_fresh(target)
        if target.exists():
            target.rmdir()  # Only an empty directory; never overwrite installed data.
        stage.rename(target)


def ensure_ports_available():
    for port in (3103, 8188, 8190, 8191):
        with socket.socket() as connection:
            connection.settimeout(0.3)
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise InstallError("Máy đang có dịch vụ dùng cổng " + str(port) + ". Nếu đã cài ViPi, hãy cập nhật từ trang quản trị.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tải và cài ViPi Server trực tiếp trên máy chủ.")
    parser.add_argument("--directory", type=Path, help="Thư mục cài mới")
    parser.add_argument("--prepare-only", action="store_true", help="Chỉ tải và chuẩn bị bộ cài, chưa khởi chạy dịch vụ")
    args = parser.parse_args(argv)
    if platform.system() != "Linux":
        raise InstallError("Hãy chạy lệnh cài trên máy Linux sẽ làm ViPi Server.")
    arch = architecture()
    target = args.directory.expanduser().absolute() if args.directory else Path.home() / ("ViPi_Server_Docker_" + arch)
    ensure_fresh(target)
    if not args.prepare_only:
        ensure_ports_available()
        if os.geteuid() != 0 and shutil.which("sudo") is None:
            raise InstallError("Cần sudo để cài đặt. Hãy nhờ quản trị viên cấp quyền.")
    info = metadata(ROOT, arch)
    target.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(target.parent).free < info["size"] * 3 + 1024**3:
        raise InstallError("Máy chưa đủ dung lượng trống để cài ViPi Server.")
    archive = download(info, Path.home() / ".cache" / "vipi" / "installers")
    print("Đang chuẩn bị bộ cài…", flush=True)
    unpack(archive, target, arch)
    print("Bộ cài đã sẵn sàng tại " + str(target), flush=True)
    if args.prepare_only:
        return 0
    command = ["sh", str(target / "install.sh")]
    if os.geteuid() != 0:
        command.insert(0, "sudo")
    subprocess.run(command, cwd=target, check=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (InstallError, OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print("Chưa cài được ViPi: " + str(error), file=sys.stderr)
        sys.exit(1)
