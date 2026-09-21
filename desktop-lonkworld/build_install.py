"""Build, test, and deliver LonkWorld without touching original prototypes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import venv

ROOT = Path(__file__).resolve().parent


def run(argv, timeout=600):
    print('Running:', ' '.join(str(arg) for arg in argv), flush=True)
    subprocess.run([str(arg) for arg in argv], cwd=ROOT, check=True, timeout=timeout,
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--desktop', type=Path, required=True)
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    desktop = args.desktop.resolve(strict=True)
    destination = desktop / 'LonkWorld XC'
    if destination.exists():
        raise RuntimeError(f'Refusing to replace an existing desktop folder: {destination}')
    shortcut = desktop/'LonkWorld XC.lnk'
    if shortcut.exists():
        raise RuntimeError(f'Refusing to replace an existing shortcut: {shortcut}')

    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    reports = ROOT/'test-reports'
    reports.mkdir(exist_ok=True)
    env_path = ROOT/'.build-env'
    if not (env_path/'Scripts/python.exe').exists():
        print('Creating isolated packaging environment', flush=True)
        venv.EnvBuilder(with_pip=True).create(env_path)
    python = env_path/'Scripts/python.exe'
    run([python, '-m', 'pip', 'install', '--disable-pip-version-check', 'pyinstaller>=6.16,<7'])
    run([python, '-m', 'PyInstaller', '--clean', '--noconfirm', '--onefile', '--windowed',
         '--name', 'LonkWorld', '--add-data', f'{ROOT / "LonkWorld.xc"}:.',
         '--distpath', ROOT/'dist', '--workpath', ROOT/'build', '--specpath', ROOT/'build',
         ROOT/'lonk_app.py'])
    exe = ROOT/'dist/LonkWorld.exe'
    if not exe.is_file() or exe.stat().st_size < 100000:
        raise RuntimeError('Packaging did not produce a valid executable artifact.')
    shutil.copy2(ROOT/'LonkWorld.xc', ROOT/'dist/LonkWorld.xc')

    # Exercise the bundled default source, actual frozen imports, TCL/TK and IO.
    for mode, args_for_mode in (('headless', ['--headless', '40']), ('gui', ['--gui-smoke'])):
        report_path = reports/f'frozen-{mode}.json'
        run([exe, *args_for_mode, '--report', report_path], timeout=120)
        report = json.loads(report_path.read_text(encoding='utf-8'))
        if report.get('ok') is not True:
            raise RuntimeError(f'Frozen {mode} verification failed: {report}')
        if mode == 'gui' and not report.get('save_roundtrip'):
            raise RuntimeError('Frozen GUI did not verify save/load.')

    destination.mkdir()
    for name, source in (('LonkWorld.exe', exe), ('LonkWorld.xc', ROOT/'LonkWorld.xc'),
                         ('README.txt', ROOT/'README.txt'), ('XC_APPLICATION_HOST.md', ROOT/'XC_APPLICATION_HOST.md'),
                         ('XC_PROCEDURES.md', ROOT/'XC_PROCEDURES.md'), ('Run LonkWorld XC.cmd', ROOT/'Run LonkWorld XC.cmd')):
        shutil.copy2(source, destination/name)
    installed_exe = destination/'LonkWorld.exe'
    if digest(installed_exe) != digest(exe) or digest(destination/'LonkWorld.xc') != digest(ROOT/'LonkWorld.xc'):
        raise RuntimeError('Desktop copy hash verification failed.')
    installed_report = reports/'desktop-smoke.json'
    run([installed_exe, '--gui-smoke', '--report', installed_report], timeout=60)
    if not json.loads(installed_report.read_text(encoding='utf-8')).get('ok'):
        raise RuntimeError('Installed desktop application failed its GUI smoke check.')

    def quote(value):
        return "'" + str(value).replace("'", "''") + "'"
    ps = ("$ws=New-Object -ComObject WScript.Shell; "
          f"$link=$ws.CreateShortcut({quote(shortcut)}); "
          f"$link.TargetPath={quote(installed_exe)}; "
          f"$link.WorkingDirectory={quote(destination)}; "
          "$link.Description='LonkWorld - one XC application'; $link.Save()")
    run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps], timeout=30)
    if not shortcut.is_file():
        raise RuntimeError('Desktop shortcut was not created.')

    receipt = {
        'ok': True, 'built_utc': datetime.now(timezone.utc).isoformat(),
        'desktop_directory': str(destination), 'executable': str(installed_exe),
        'application_source': str(destination/'LonkWorld.xc'), 'shortcut': str(shortcut),
        'exe_sha256': digest(installed_exe), 'source_sha256': digest(destination/'LonkWorld.xc'),
        'checks': ['frozen 40 ticks',
                   'frozen GUI and save/load', 'installed GUI and save/load', 'desktop copy hashes'],
        'launch_requested': args.launch,
    }
    if args.launch:
        flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
        with open(os.devnull, 'rb') as null_in, open(os.devnull, 'wb') as null_out:
            process = subprocess.Popen([str(installed_exe)], cwd=destination,
                                       stdin=null_in, stdout=null_out, stderr=null_out,
                                       close_fds=True, creationflags=flags)
        time.sleep(3)
        receipt['launched_pid'] = process.pid
        receipt['launch_alive_after_3_seconds'] = process.poll() is None
        if process.poll() is not None:
            raise RuntimeError(f'Application exited immediately after launch: {process.returncode}')
    (ROOT/'build-receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    (destination/'verification.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
