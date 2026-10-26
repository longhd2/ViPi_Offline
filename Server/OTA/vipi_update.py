#!/usr/bin/env python3
"""Host-side transactional ViPi Docker updater; Python standard library only."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid


class UpdateError(RuntimeError):
    pass


def run(args, timeout=120):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        # Docker diagnostics may contain environment values: keep them off stdout.
        raise UpdateError(f'{args[0]} {args[1]} failed (exit {p.returncode})')
    return p.stdout.strip()


def atomic_json(path, value):
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w') as f:
        os.chmod(tmp, 0o600)
        json.dump(value, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def inspect(container):
    return json.loads(run(['docker', 'inspect', container]))[0]


def validate_reference(ref):
    local = re.fullmatch(r'sha256:[0-9a-f]{64}', ref)
    remote = re.fullmatch(r'ghcr\.io/longhd2/vipi-server@sha256:[0-9a-f]{64}', ref)
    if not (local or remote):
        raise UpdateError('Use a local sha256 image ID or pinned ghcr.io/longhd2/vipi-server@sha256 digest')
    return bool(remote)


def tree_bytes(root):
    return sum(p.stat().st_size for p in root.rglob('*')
               if p.is_file() and not p.is_symlink()) if root.exists() else 0


def copy_tree(source, target):
    # Never follow symlinks into unrelated folders or secrets.
    shutil.copytree(source, target, symlinks=True, copy_function=shutil.copy2)
    shutil.copystat(source, target)
    for p in [target, *target.rglob('*')]:
        st = (source / p.relative_to(target)).lstat()
        os.chown(p, st.st_uid, st.st_gid, follow_symlinks=False)


class Updater:
    def __init__(self, root, container, timeout):
        self.root = root.resolve()
        self.container = container
        self.timeout = timeout
        self.state = self.root / '.vipi-ota'
        # Compose also loads this file for the user's normal `compose up` command.
        self.override = self.root / 'compose.override.yaml'
        self.compose = self.root / 'compose.yaml'
        self.tx_path = self.state / 'transaction.json'
        if not self.compose.is_file():
            raise UpdateError('compose.yaml is missing; native service needs a separate migration')
        try:
            current = inspect(container)
        except UpdateError:
            # A power loss can occur between removing the old container and
            # creating the new one. Recover from the root-private journal.
            if not self.tx_path.exists():
                raise
            tx = json.loads(self.tx_path.read_text())
            if (tx.get('container') != container or tx.get('root') != str(self.root)
                    or tx.get('phase') in ('committed', 'rolled_back')):
                raise
            current = {'Config': {'Labels': {
                'com.docker.compose.project.working_dir': str(self.root),
                'com.docker.compose.project': tx['project'],
                'com.docker.compose.service': tx['service']}},
                'Mounts': [{'Type': 'bind', 'Source': str(self.root / n), 'Destination': d}
                           for n, d in [('config', '/var/lib/vipi/config'), ('data', '/app/data'),
                                        ('plugins', '/app/skills/plugins')]]}
        labels = current['Config'].get('Labels') or {}
        if Path(labels.get('com.docker.compose.project.working_dir', '/')).resolve() != self.root:
            raise UpdateError('Container does not belong to this installation directory')
        self.project = labels['com.docker.compose.project']
        self.service = labels['com.docker.compose.service']
        self.current = current
        if self.override.exists():
            try:
                value = json.loads(self.override.read_text())
                if value != {'services': {self.service: {'image': value['services'][self.service]['image']}}}:
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                raise UpdateError('Existing custom Compose override needs manual integration') from None
        for name, dest in [('config', '/var/lib/vipi/config'), ('data', '/app/data'),
                           ('plugins', '/app/skills/plugins')]:
            mount = next((m for m in current['Mounts'] if m['Destination'] == dest), None)
            if not mount or mount['Type'] != 'bind' or Path(mount['Source']).resolve() != self.root / name:
                raise UpdateError(f'Expected external bind mount for {name}')
        # Migration transactions are local/private; never include in release archives.

    def compose_run(self, *args):
        return run(['docker', 'compose', '--project-directory', str(self.root),
                    '-p', self.project, '-f', str(self.compose), '-f', str(self.override),
                    *args], timeout=max(120, self.timeout))

    def select_image(self, image):
        atomic_json(self.override, {'services': {self.service: {'image': image}}})

    def healthy(self):
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            c = inspect(self.container)
            state = c['State']
            if state.get('Status') in ('exited', 'dead'):
                raise UpdateError('Candidate stopped before readiness')
            if c.get('RestartCount', 0) > 1:
                raise UpdateError('Candidate repeatedly crashed during startup')
            if state.get('Health', {}).get('Status') == 'healthy':
                return
            if state.get('Health', {}).get('Status') == 'unhealthy':
                raise UpdateError('Candidate healthcheck failed')
            time.sleep(2)
        raise UpdateError('Readiness deadline exceeded')

    def snapshot(self, path):
        path.mkdir(mode=0o700)
        for name in ['config', 'data', 'plugins']:
            copy_tree(self.root / name, path / name)

    def restore(self, path, tx):
        # Retain candidate data for diagnosis instead of deleting anything.
        failed = self.state / ('failed-' + uuid.uuid4().hex)
        failed.mkdir(mode=0o700)
        # Stage copies first so a full disk leaves the live trees untouched.
        staged = self.state / ('restore-' + uuid.uuid4().hex)
        self.snapshot_from(path, staged)
        for name in ['config', 'data', 'plugins']:
            live = self.root / name
            tx['restore_step'] = name
            tx['restore_staged'] = str(staged)
            tx['restore_failed'] = str(failed)
            atomic_json(self.tx_path, tx)
            if live.exists():
                live.rename(failed / name)
            (staged / name).rename(live)

    def snapshot_from(self, source, target):
        target.mkdir(mode=0o700)
        for name in ['config', 'data', 'plugins']:
            copy_tree(source / name, target / name)

    def revert(self, tx):
        self.select_image(tx['old_image'])
        self.compose_run('stop', self.service)
        self.restore(Path(tx['snapshot']), tx)
        self.compose_run('up', '-d', '--no-deps', '--force-recreate', '--pull', 'never', self.service)
        self.healthy()
        tx['phase'] = 'rolled_back'
        atomic_json(self.tx_path, tx)

    def apply(self, ref):
        remote = validate_reference(ref)
        if self.tx_path.exists():
            tx = json.loads(self.tx_path.read_text())
            if tx['phase'] not in ('committed', 'rolled_back'):
                raise UpdateError('Unfinished transaction: run --recover first')
        if shutil.disk_usage(self.root).free < 512 * 1024**2:
            raise UpdateError('Need at least 512 MiB free before preparing update')
        if remote:
            # Running server stays up throughout downloads.
            run(['docker', 'pull', ref], timeout=1800)
        candidate = json.loads(run(['docker', 'image', 'inspect', ref]))[0]
        arch = {'aarch64': 'arm64', 'x86_64': 'amd64'}.get(platform.machine())
        if not arch or candidate.get('Architecture') != arch or candidate.get('Os') != 'linux':
            raise UpdateError('Candidate architecture differs from host')
        if not candidate['Config'].get('Healthcheck', {}).get('Test'):
            raise UpdateError('Candidate has no healthcheck')
        old = inspect(self.container)
        if candidate['Id'] == old['Image']:
            print('Already running this image; no restart needed', flush=True)
            return
        size = sum(tree_bytes(self.root / n) for n in ['config', 'data', 'plugins'])
        if shutil.disk_usage(self.root).free < size * 3 + 256 * 1024**2:
            raise UpdateError('Insufficient disk for update and rollback snapshots')
        tx = {'phase': 'prepared', 'old_image': old['Image'], 'new_image': candidate['Id'],
              'root': str(self.root), 'container': self.container, 'project': self.project, 'service': self.service,
              'snapshot': str(self.state / ('snapshot-' + uuid.uuid4().hex))}
        self.select_image(old['Image'])
        # Check Compose syntax before stopping a running server.
        self.compose_run('config', '--quiet')
        atomic_json(self.tx_path, tx)
        self.compose_run('stop', self.service)
        try:
            self.snapshot(Path(tx['snapshot']))
        except Exception:
            self.compose_run('up', '-d', '--no-deps', '--pull', 'never', self.service)
            self.healthy()
            tx['phase'] = 'rolled_back'
            atomic_json(self.tx_path, tx)
            raise
        tx['phase'] = 'switching'
        atomic_json(self.tx_path, tx)
        try:
            self.select_image(candidate['Id'])
            self.compose_run('up', '-d', '--no-deps', '--force-recreate', '--pull', 'never', self.service)
            self.healthy()
            tx['phase'] = 'committed'
            atomic_json(self.tx_path, tx)
            print('Update healthy; configuration and API retained', flush=True)
        except Exception as exc:
            print('Candidate failed; restoring previous version', flush=True)
            self.revert(tx)
            raise UpdateError(f'Update failed ({type(exc).__name__}); previous version is healthy') from None

    def recover(self):
        tx = json.loads(self.tx_path.read_text())
        if tx['phase'] == 'rolled_back':
            print('Previous version already restored')
            return
        if tx['phase'] == 'prepared':
            self.select_image(tx['old_image'])
            self.compose_run('up', '-d', '--no-deps', '--pull', 'never', self.service)
            self.healthy()
            tx['phase'] = 'rolled_back'
            atomic_json(self.tx_path, tx)
        else:
            self.revert(tx)
        print('Previous version restored and healthy')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--container', default='vipi-server')
    parser.add_argument('--timeout', type=int, default=180)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--status', action='store_true')
    action.add_argument('--image')
    action.add_argument('--recover', action='store_true')
    args = parser.parse_args()
    updater = Updater(args.root, args.container, args.timeout)
    if args.status:
        c = updater.current
        print(json.dumps({'architecture': platform.machine(), 'image': c['Image'],
                          'health': c['State'].get('Health', {}).get('Status'),
                          'free_mib': shutil.disk_usage(args.root).free // 1024**2}))
        return
    if os.geteuid() != 0:
        raise UpdateError('Run updater with sudo')
    updater.state.mkdir(mode=0o700, exist_ok=True)
    os.chmod(updater.state, 0o700)
    with (updater.state / 'lock').open('a') as lock:
        os.chmod(updater.state / 'lock', 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise UpdateError('Another update is in progress') from None
        if args.recover:
            updater.recover()
        else:
            updater.apply(args.image)


if __name__ == '__main__':
    try:
        main()
    except (UpdateError, subprocess.TimeoutExpired, OSError) as error:
        print(f'UPDATE ERROR: {error}', file=sys.stderr)
        sys.exit(1)
