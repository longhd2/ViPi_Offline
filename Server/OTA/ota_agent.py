#!/usr/bin/env python3
"""Small host agent: signed release packages, no host control in the web process."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
from urllib.parse import urlsplit
import urllib.request
import uuid
from vipi_update import Updater, UpdateError, atomic_json, inspect, run

CHANNEL = 'https://raw.githubusercontent.com/longhd2/ViPi_Offline/main/Server/updates/stable.json'
ARCH = {'x86_64': 'amd64', 'aarch64': 'arm64'}.get(platform.machine())
BASE = {'amd64': 'sha256:131d6ffcbc7c181ce4634ecffe57cd9233d190e8db12dfc786fd444d473759a6',
        'arm64': 'sha256:eef042eaed0900b83f4d6ae412fd058ec066d1e233772378137d17f19c093bf7'}


def version_key(value):
    """The numeric release series follows every legacy dated release."""
    if not isinstance(value, str):
        raise UpdateError('Định dạng phiên bản không hợp lệ')
    if not value:
        return (-1,)
    if re.fullmatch(r'(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})', value) and not re.fullmatch(r'20[0-9]{2}\.[0-9]{2}\.[0-9]{2}', value):
        return (1, *map(int, value.split('.')))
    match = re.fullmatch(r'(20[0-9]{2})\.([0-9]{2})\.([0-9]{2})(?:-ota([0-9]{3}))?', value)
    if match:
        from datetime import date
        year, month, day = map(int, match.groups()[:3])
        try:
            date(year, month, day)
        except ValueError:
            raise UpdateError('Định dạng phiên bản không hợp lệ') from None
        return (0, year, month, day, int(match[4] or 0))
    raise UpdateError('Định dạng phiên bản không hợp lệ')


def valid_release_version(value):
    try:
        key = version_key(value)
        return key[0] == 1 or (key[0] == 0 and '-ota' in value)
    except UpdateError:
        return False


def valid_download_url(url):
    p = urlsplit(url)
    return (p.scheme == 'https' and p.hostname == 'github.com' and not p.username and
            not p.password and p.port in (None, 443) and not p.query and not p.fragment and
            p.path.startswith('/longhd2/ViPi_Offline/releases/download/') and
            '..' not in p.path and '%' not in p.path)


def download(url, dest, limit, expected=None, progress=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'ViPi-OTA/1', 'Cache-Control': 'no-cache'})
    digest = hashlib.sha256()
    count = 0
    with urllib.request.urlopen(request, timeout=30) as response, dest.open('wb') as out:
        final = urlsplit(response.url)
        if final.scheme != 'https' or final.hostname not in ('github.com', 'raw.githubusercontent.com',
                'release-assets.githubusercontent.com', 'objects.githubusercontent.com'):
            raise UpdateError('Địa chỉ tải xuống không hợp lệ')
        while True:
            chunk = response.read(256 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > limit:
                raise UpdateError('Gói cập nhật vượt kích thước cho phép')
            out.write(chunk)
            digest.update(chunk)
            if progress:
                progress(count)
    if expected and (count != expected['size'] or digest.hexdigest() != expected['sha256']):
        raise UpdateError('Mã kiểm tra gói cập nhật không khớp')


def verify_manifest(manifest_path, signature, public_key):
    p = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(public_key),
                        '-rawin', '-in', str(manifest_path), '-sigfile', str(signature)],
                       capture_output=True, timeout=15)
    if p.returncode:
        raise UpdateError('Chữ ký bản cập nhật không hợp lệ')
    if manifest_path.stat().st_size > 65536:
        raise UpdateError('Thông tin cập nhật quá lớn')
    data = json.loads(manifest_path.read_text())
    if data.get('schema') != 1 or not valid_release_version(data.get('version')):
        raise UpdateError('Định dạng phiên bản không hợp lệ')
    if not isinstance(data.get('expires_at'), (int, float)) or not time.time() < data['expires_at'] < time.time() + 370 * 86400:
        raise UpdateError('Thông tin cập nhật hết hạn; kiểm tra ngày giờ máy chủ')
    if not isinstance(data.get('platforms'), dict):
        raise UpdateError('Thông tin kiến trúc không hợp lệ')
    item = data['platforms'].get(ARCH)
    if not isinstance(item, dict):
        raise UpdateError('Thiếu gói cập nhật phù hợp')
    if not item or not valid_download_url(item.get('url', '')):
        raise UpdateError('Không có gói phù hợp với máy này')
    if not re.fullmatch(r'[0-9a-f]{64}', str(item.get('sha256', ''))):
        raise UpdateError('Mã kiểm tra không hợp lệ')
    if not isinstance(item.get('size'), int) or not 0 < item['size'] <= 128 * 1024**2:
        raise UpdateError('Kích thước gói không hợp lệ')
    if item.get('runtime') != 'py313-202610-' + ARCH:
        raise UpdateError('Bản này cần nâng cấp bộ nền trước')
    return data


def unpack_package(archive, dest):
    total = 0
    allowed = {'.so', '.json', '.html', '.css', '.js', '.svg', '.png', '.ico', '.woff2', '.yaml'}
    seen = set()
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            path = PurePosixPath(member.name)
            runtime_wheel = (len(path.parts) == 2 and path.parts[0] == 'runtime' and
                             path.name == 'av-19.0.2-cp312-abi3-manylinux_2_28_' + {'amd64': 'x86_64', 'arm64': 'aarch64'}[ARCH] + '.whl')
            app_file = (len(path.parts) >= 2 and path.parts[0] == 'app' and path.suffix in allowed)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts or
                    not (app_file or runtime_wheel) or member.name in seen or
                    any(x in path.parts for x in ('.git', 'secrets.yaml')) or
                    (path.suffix == '.yaml' and path.name not in ('manifest.yaml', 'system_catalog.yaml'))):
                raise UpdateError('Nội dung gói cập nhật không hợp lệ')
            seen.add(member.name)
            total += member.size
            if total > 256 * 1024**2 or len(seen) > 4096:
                raise UpdateError('Gói cập nhật giải nén vượt giới hạn')
            out = dest / str(path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source, out.open('xb') as target:
                shutil.copyfileobj(source, target)
            out.chmod(0o644)
    if not any(n.startswith('app/web/update_api.') and n.endswith('.so') for n in seen):
        raise UpdateError('Thiếu thành phần cập nhật trong gói')


class Agent:
    def __init__(self, config):
        self.config = config
        self.root = Path(config['root']).resolve()
        self.container = config.get('container', 'vipi-server')
        self.state = self.root / '.vipi-ota'
        self.state.mkdir(mode=0o700, exist_ok=True)
        self.state.chmod(0o700)
        self.queue = self.root / 'runtime/ota'
        self.queue.mkdir(parents=True, exist_ok=True)
        (self.queue / 'requests').mkdir(exist_ok=True)
        for p in [self.queue, self.queue / 'requests']:
            p.chmod(0o700)
            os.chown(p, 1000, 1000)
        self.key = Path(config['public_key'])
        self.status = {'phase': 'ready', 'busy': False, 'message': 'Sẵn sàng kiểm tra cập nhật.'}
        self.release = None
        self.last_check = 0
        try:
            self.refresh_current()
        except UpdateError:
            tx = self.state / 'transaction.json'
            if not tx.exists() or json.loads(tx.read_text()).get('phase') in ('committed', 'rolled_back'):
                raise
            self.current = None

    def refresh_current(self):
        c = inspect(self.container)
        self.current = c
        self.status['current_version'] = (c['Config'].get('Labels') or {}).get('org.vipi.version', '2026.10.16')
        tx = self.state / 'transaction.json'
        self.status['rollback_available'] = False
        if tx.exists():
            data = json.loads(tx.read_text())
            if data.get('phase') != 'rolled_back':
                # Bootstrap rollback remains available via CLI; web requires the old UI too.
                try:
                    old = json.loads(run(['docker', 'image', 'inspect', data['old_image']]))[0]
                    self.status['rollback_available'] = bool((old['Config'].get('Labels') or {}).get('org.vipi.version'))
                except UpdateError:
                    pass

    def publish(self, **changes):
        self.status.update(changes, heartbeat=time.time())
        atomic_json(self.queue / 'status.json', self.status)
        os.chown(self.queue / 'status.json', 1000, 1000)

    def check(self):
        self.publish(phase='checking', busy=True, message='Đang kiểm tra phiên bản và chữ ký…')
        manifest = self.state / 'release.json'
        sig = self.state / 'release.sig'
        # Local manifests are a root-only test harness option, never accepted from the web.
        if self.config.get('test_manifest'):
            shutil.copyfile(self.config['test_manifest'], manifest)
            shutil.copyfile(self.config['test_manifest'] + '.sig', sig)
        else:
            download(CHANNEL, manifest, 65536)
            download(CHANNEL + '.sig', sig, 1024)
        release = verify_manifest(manifest, sig, self.key)
        self.refresh_current()
        old = self.state / 'highest-seen.json'
        highest = json.loads(old.read_text()).get('version', '') if old.exists() else ''
        if version_key(release['version']) < version_key(highest):
            raise UpdateError('Thông tin phiên bản cũ hơn lần kiểm tra trước')
        atomic_json(old, {'version': release['version']})
        self.release = release
        self.last_check = time.monotonic()
        available = version_key(release['version']) > version_key(self.status['current_version'])
        self.publish(phase='ready', busy=False, latest_version=release['version'], update_available=available,
                     message='Có phiên bản mới, bạn có thể cập nhật.' if available else 'ViPi đang ở phiên bản mới nhất.')

    def apply(self):
        self.check()
        if not self.status['update_available']:
            return
        release = self.release
        item = release['platforms'][ARCH]
        labels = self.current['Config'].get('Labels') or {}
        runtime = labels.get('org.vipi.runtime')
        if runtime != item['runtime'] and self.current['Image'] != BASE.get(ARCH):
            raise UpdateError('Bản nền chưa tương thích với cập nhật này')
        if shutil.disk_usage(self.root).free < 512 * 1024**2:
            raise UpdateError('Cần ít nhất 512 MB trống để cập nhật')
        self.publish(phase='downloading', busy=True, message='Đang tải gói cập nhật. ViPi cũ vẫn hoạt động.')
        with tempfile.TemporaryDirectory(prefix='package-', dir=self.state) as tmp:
            tmp = Path(tmp)
            package = tmp / 'package.tar.gz'
            def progress(count):
                self.publish(message=f'Đang tải gói cập nhật: {count // 1024} / {item["size"] // 1024} KB')
            download(item['url'], package, item['size'], item, progress)
            unpack_package(package, tmp)
            self.publish(phase='preparing', message='Đang chuẩn bị phiên bản mới…')
            base_tag = 'vipi-ota-base:' + self.current['Image'][7:23]
            run(['docker', 'tag', self.current['Image'], base_tag])
            dependencies = ''
            if (tmp / 'runtime').is_dir():
                dependencies = ('USER root\nCOPY runtime/ /tmp/vipi-runtime/\n'
                                'RUN python -m pip install --no-index --no-deps /tmp/vipi-runtime/*.whl '
                                '&& rm -rf /tmp/vipi-runtime\nUSER vipi\n')
            (tmp / 'Dockerfile').write_text('FROM ' + base_tag + '\n' + dependencies +
                'LABEL org.vipi.version="' + release['version'] + '" org.vipi.runtime="' + item['runtime'] + '"\n' +
                'COPY --chown=1000:1000 app/ /app/\n')
            tag = 'vipi-server:ota-' + release['version'] + '-' + ARCH
            run(['docker', 'build', '--network', 'none', '-q', '-t', tag, str(tmp)], timeout=300)
            candidate = json.loads(run(['docker', 'image', 'inspect', tag]))[0]
            self.publish(phase='switching', message='Đang chuyển phiên bản. ViPi sẽ kết nối lại sau ít phút.')
            Updater(self.root, self.container, 240).apply(candidate['Id'])
        self.refresh_current()
        self.publish(phase='ready', busy=False, update_available=False, message='Cập nhật thành công. ViPi đã sẵn sàng.')

    def rollback(self):
        self.refresh_current()
        if not self.status['rollback_available']:
            raise UpdateError('Chưa có phiên bản trước để khôi phục qua web')
        self.publish(phase='rollback', busy=True, message='Đang khôi phục phiên bản và dữ liệu trước cập nhật…')
        Updater(self.root, self.container, 240).recover()
        self.refresh_current()
        self.publish(phase='ready', busy=False, update_available=False, message='Đã khôi phục phiên bản trước.')

    def recover_interrupted(self):
        tx = self.state / 'transaction.json'
        if tx.exists() and json.loads(tx.read_text()).get('phase') not in ('committed', 'rolled_back'):
            self.publish(phase='rollback', busy=True, message='Đang phục hồi lần cập nhật bị gián đoạn…')
            Updater(self.root, self.container, 240).recover()
            self.refresh_current()

    def once(self):
        for p in sorted((self.queue / 'requests').glob('*.json'))[:8]:
            if not re.fullmatch(r'[0-9a-f]{32}\.json', p.name):
                continue
            try:
                fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(fd) as f:
                    st = os.fstat(f.fileno())
                    if not stat.S_ISREG(st.st_mode) or st.st_size > 512:
                        raise ValueError()
                    request = json.load(f)
                p.unlink()
                if request.get('id') != p.stem or request.get('action') not in ('check', 'apply', 'rollback'):
                    raise ValueError()
                getattr(self, {'check': 'check', 'apply': 'apply', 'rollback': 'rollback'}[request['action']])()
            except (OSError, ValueError, KeyError, UpdateError, subprocess.TimeoutExpired):
                # No remote URLs, secrets or raw Docker errors exposed in status.
                self.refresh_current()
                self.publish(phase='error', busy=False, message='Chưa cập nhật được. Bản đang chạy được giữ lại hoặc đã tự khôi phục. Kiểm tra Internet, dung lượng và bản phát hành rồi thử lại.')
        self.publish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    agent = Agent(config)
    with (agent.state / 'agent.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        agent.recover_interrupted()
        agent.publish(busy=False)
        while True:
            agent.once()
            if args.once:
                break
            time.sleep(2)


if __name__ == '__main__':
    main()
