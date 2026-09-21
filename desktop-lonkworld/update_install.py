"""Verify the social-life release, then back up and update the desktop install."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from build_install import ROOT, digest, run


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def build():
    python = ROOT/'.build-env/Scripts/python.exe'
    run([python, '-m', 'PyInstaller', '--clean', '--noconfirm', '--onefile', '--windowed',
         '--name', 'LonkWorld', '--add-data', f'{ROOT / "LonkWorld.xc"}:.',
         '--distpath', ROOT/'dist', '--workpath', ROOT/'build', '--specpath', ROOT/'build',
         ROOT/'lonk_app.py'])
    exe = ROOT/'dist/LonkWorld.exe'
    # Test beside the current source; never pick up the previous release's source.
    shutil.copy2(ROOT/'LonkWorld.xc', ROOT/'dist/LonkWorld.xc')
    reports = ROOT/'test-reports'
    reports.mkdir(exist_ok=True)
    for name, mode in [('headless', ['--headless', '40']), ('gui', ['--gui-smoke'])]:
        report = reports/f'update-frozen-{name}.json'
        if report.exists():
            report.unlink()
        run([exe, *mode, '--report', report], timeout=180)
        data = json.loads(report.read_text(encoding='utf-8'))
        if data.get('ok') is not True or name == 'gui' and not data.get('save_roundtrip'):
            raise RuntimeError(f'Frozen {name} verification failed: {data}')
    receipt = {'exe_sha256': digest(exe), 'source_sha256': digest(ROOT/'LonkWorld.xc'),
               'built_utc': datetime.now(timezone.utc).isoformat(),
               'checks': ['frozen 40 ticks', 'frozen GUI and save/load']}
    (reports/'update-build.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2), flush=True)


def install(desktop, launch):
    desktop = desktop.resolve(strict=True)
    destination = (desktop/'LonkWorld XC').resolve()
    if destination.parent != desktop:
        raise RuntimeError('Desktop installation resolves outside the requested Desktop.')
    receipt = json.loads((ROOT/'test-reports/update-build.json').read_text(encoding='utf-8'))
    exe = ROOT/'dist/LonkWorld.exe'
    if digest(exe) != receipt['exe_sha256'] or digest(ROOT/'LonkWorld.xc') != receipt['source_sha256']:
        raise RuntimeError('The build changed after verification; build again before installing.')
    missing_installation = not destination.exists()
    if not missing_installation:
        old_receipt = json.loads((destination/'verification.json').read_text(encoding='utf-8'))
        if digest(destination/'LonkWorld.xc') != old_receipt['source_sha256']:
            raise RuntimeError('The installed XC source was edited. Preserve and reconcile those edits before updating.')
    installed_exe = destination/'LonkWorld.exe'
    # Ask only this application to close normally, allowing its close handler to save.
    ps = (f"$target={quote(installed_exe)}; "
          "$apps=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {$_.ExecutablePath -eq $target}); "
          "foreach ($app in $apps) { $p=Get-Process -Id $app.ProcessId -ErrorAction SilentlyContinue; "
          "if ($p -and $p.MainWindowHandle -ne 0) { [void]$p.CloseMainWindow() } }; "
          "$end=(Get-Date).AddSeconds(25); do { Start-Sleep -Milliseconds 300; "
          "$left=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {$_.ExecutablePath -eq $target}) "
          "} while ($left.Count -gt 0 -and (Get-Date) -lt $end); "
          "if ($left.Count -gt 0) { throw 'LonkWorld is still open. Close its window normally, then retry installation.' }")
    run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps], timeout=40)
    destination.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    backup = destination/'backups'/stamp
    backup.mkdir(parents=True, exist_ok=False)
    names = ['LonkWorld.exe', 'LonkWorld.xc', 'README.txt', 'XC_APPLICATION_HOST.md',
             'XC_PROCEDURES.md', 'Run LonkWorld XC.cmd', 'verification.json']
    previously_present = {name for name in names if (destination/name).is_file()}
    for name in names:
        if name in previously_present:
            shutil.copy2(destination/name, backup/name)
    save = Path(os.environ['LOCALAPPDATA'])/'LonkWorldXC/world.json'
    if save.exists():
        shutil.copy2(save, backup/'world.json')
        from lonk_engine import LonkWorld
        from xc_app_runtime import XCApplication
        world = LonkWorld.load(save, controller=XCApplication(ROOT/'LonkWorld.xc'))
        receipt['existing_world_tick'] = world.tick
        receipt['existing_world_population'] = len(world.lonks)
        receipt['existing_world_migration_verified'] = True
    # Each replaced file has an intact backup. Roll back the installed files on failure.
    try:
        for name in names[:-1]:
            source = exe if name == 'LonkWorld.exe' else ROOT/name
            pending = destination/(name+'.update')
            shutil.copy2(source, pending)
            os.replace(pending, destination/name)
        if digest(installed_exe) != receipt['exe_sha256'] or digest(destination/'LonkWorld.xc') != receipt['source_sha256']:
            raise RuntimeError('Installed files failed hash verification.')
        report = ROOT/'test-reports/update-desktop.json'
        if report.exists():
            report.unlink()
        run([installed_exe, '--gui-smoke', '--report', report], timeout=90)
        if json.loads(report.read_text(encoding='utf-8')).get('ok') is not True:
            raise RuntimeError('Installed GUI verification failed.')
    except Exception:
        for name in names:
            if name in previously_present:
                shutil.copy2(backup/name, destination/name)
            elif (destination/name).exists():
                (destination/name).unlink()
        raise
    receipt.update(ok=True, release='2.0', backup=str(backup), executable=str(installed_exe),
                   restored_missing_installation=missing_installation,
                   application_source=str(destination/'LonkWorld.xc'))
    receipt['checks'] += ['installed GUI and save/load', 'desktop copy hashes']
    if launch:
        flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
        with open(os.devnull, 'rb') as null_in, open(os.devnull, 'wb') as null_out:
            process = subprocess.Popen([str(installed_exe)], cwd=destination, stdin=null_in,
                                       stdout=null_out, stderr=null_out, close_fds=True, creationflags=flags)
        time.sleep(3)
        receipt['launched_pid'] = process.pid
        receipt['launch_alive_after_3_seconds'] = process.poll() is None
        if process.poll() is not None:
            raise RuntimeError('Updated application exited immediately after launch.')
    for path in [destination/'verification.json', ROOT/'update-receipt.json']:
        path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', type=Path, metavar='DESKTOP')
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if args.install:
        install(args.install, args.launch)
    else:
        build()
