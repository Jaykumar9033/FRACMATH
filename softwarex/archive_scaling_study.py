"""Package complete scaling cases, or extract their inspectable evidence.

Proprietary binaries and ODBs are excluded. Archives retain the workspace paths
used by analyze_scaling_study.py; no Abaqus installation is needed to analyze.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from run_scaling_study import SIZES, MESHES, CONFIGS

KEEP = {'.txt', '.csv', '.json', '.mat', '.inp', '.dat', '.msg', '.sta',
        '.log', '.m', '.py', '.for', '.env'}


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def pack(workspace, output):
    summary = json.loads((workspace / 'analysis/summary.json').read_text())
    if summary.get('missing'):
        raise ValueError('Analyze all completed runs before archiving')
    cases = [(s, m) for s in SIZES for m in MESHES]
    for size, mesh in cases:
        for config in CONFIGS:
            if not (workspace / size / mesh / config / 'completed.json').exists():
                raise ValueError('Incomplete case: ' + '/'.join([size, mesh, config]))
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for size, mesh in cases:
        case = workspace / size / mesh
        archive = output / (size + '_' + mesh + '.zip')
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as zipped:
            for path in sorted(case.rglob('*')):
                if path.is_file() and path.suffix.lower() in KEEP:
                    name = path.relative_to(workspace).as_posix()
                    hashes[name] = digest(path)
                    zipped.write(path, name)
        if archive.stat().st_size >= 95 * 1024**2:
            raise ValueError('Archive exceeds repository size budget: ' + str(archive))
    for name in ['manifest.json', 'matlab_reuse_manifest.json', 'reuse_manifest.json']:
        if (workspace / name).exists():
            shutil.copy2(workspace / name, output / name)
    shutil.copytree(workspace / 'source_snapshot', output / 'source_snapshot', dirs_exist_ok=True)
    shutil.copytree(workspace / 'analysis', output / 'analysis', dirs_exist_ok=True)
    archives = {p.name: digest(p) for p in sorted(output.glob('*.zip'))}
    support = {p.relative_to(output).as_posix(): digest(p)
               for p in sorted(output.rglob('*'))
               if p.is_file() and p.suffix != '.zip' and p.name != 'SHA256.json'}
    (output / 'SHA256.json').write_text(json.dumps(
        {'archives': archives, 'members': hashes, 'support': support},
        indent=2) + '\n', encoding='utf-8')


def extract(package, workspace):
    manifest = json.loads((package / 'SHA256.json').read_text())
    for name, expected in manifest['support'].items():
        if digest(package / name) != expected:
            raise ValueError('Support file hash mismatch: ' + name)
    workspace.mkdir(parents=True, exist_ok=True)
    for name, expected in manifest['archives'].items():
        archive = package / name
        if digest(archive) != expected:
            raise ValueError('Archive hash mismatch: ' + name)
        with zipfile.ZipFile(archive) as zipped:
            for entry in zipped.infolist():
                target = (workspace / entry.filename).resolve()
                if not target.is_relative_to(workspace.resolve()):
                    raise ValueError('Archive path escapes workspace')
                if not entry.is_dir():
                    if target.exists():
                        if digest(target) != manifest['members'][entry.filename]:
                            raise ValueError('Existing file differs: ' + str(target))
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zipped.open(entry) as source, target.open('wb') as dest:
                        shutil.copyfileobj(source, dest)
                    if digest(target) != manifest['members'][entry.filename]:
                        raise ValueError('Extracted member hash mismatch')
    for name in ['manifest.json', 'matlab_reuse_manifest.json', 'reuse_manifest.json']:
        if (package / name).exists():
            shutil.copy2(package / name, workspace / name)
    shutil.copytree(package / 'source_snapshot', workspace / 'source_snapshot', dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['pack', 'extract'])
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'pack':
        pack(args.workspace.resolve(), args.package.resolve())
    else:
        extract(args.package.resolve(), args.workspace.resolve())


if __name__ == '__main__':
    main()
