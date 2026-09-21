"""Create a portable release ZIP from the verified local build."""
import argparse
import json
from pathlib import Path
import zipfile
from build_install import ROOT, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'release-assets/LonkWorld-XC-Windows-x64.zip')
    args = parser.parse_args()
    receipt = json.loads((ROOT/'test-reports/update-build.json').read_text(encoding='utf-8'))
    exe = ROOT/'dist/LonkWorld.exe'
    if digest(exe) != receipt['exe_sha256'] or digest(ROOT/'LonkWorld.xc') != receipt['source_sha256']:
        raise RuntimeError('Build differs from verified artifacts; rebuild before packaging.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    files = {'LonkWorld.exe': exe}
    for name in ('LonkWorld.xc', 'README.txt', 'XC_APPLICATION_HOST.md', 'XC_PROCEDURES.md', 'Run LonkWorld XC.cmd'):
        files[name] = ROOT/name
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, path in files.items():
            archive.write(path, 'LonkWorld XC/'+name)
        archive.writestr('LonkWorld XC/verification.json', json.dumps(receipt, indent=2))
    with zipfile.ZipFile(args.output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('ZIP integrity check failed')
    print(json.dumps({'file': str(args.output), 'bytes': args.output.stat().st_size,
                      'sha256': digest(args.output)}, indent=2))


if __name__ == '__main__':
    main()
