"""Record the actual exact shared runtime; no biological workflow execution."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

args = argparse.ArgumentParser()
args.add_argument('--cli-tag', required=True)
args.add_argument('--cli-commit', required=True)
selected = args.parse_args()
ROOT = Path('/fsx/work/pangenome_runtime/20261020')
DRIVER = Path('/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.04')
os.environ['PATH'] = ':'.join(map(str, [ROOT / 'bin', DRIVER / 'bin', ROOT / 'env/bin'])) + ':' + os.environ['PATH']
os.environ['TMPDIR'] = str(ROOT / 'tmp')

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

tools = {}
for name, args in {
    'sentieon-cli': ['sentieon-cli', '--version'],
    'sentieon': ['sentieon', 'driver', '--version'],
    'samtools': ['samtools', '--version'],
    'bcftools': ['bcftools', '--version'],
    'bedtools': ['bedtools', '--version'],
    'mosdepth': ['mosdepth', '--version'],
    'vg': ['vg', 'version'],
    'kmc': ['kmc'],
}.items():
    executable = shutil.which(args[0])
    if not executable:
        raise RuntimeError(f'Missing {name}')
    result = subprocess.run(args, capture_output=True, timeout=60)
    banner = (result.stdout + result.stderr).decode('utf-8', errors='replace')
    if name != 'kmc' and result.returncode:
        raise RuntimeError(f'{name} version probe failed')
    tools[name] = dict(executable=executable, sha256=digest(executable),
                        version_banner=banner[:4096], probe_rc=result.returncode)
assert tools['sentieon-cli']['version_banner'].strip() == selected.cli_tag
assert subprocess.check_output(['git', '-C', str(ROOT / ('cli-' + selected.cli_tag)), 'rev-parse', 'HEAD'], text=True).strip() == selected.cli_commit
assert '202503.04' in tools['sentieon']['version_banner']
assert 'v1.73.0' in tools['vg']['version_banner']
assert tools['vg']['sha256'] == 'd5752977237e801d971f0d044f43fde4f3005da35f0451b4f452d1c1c9b8414b'
from sentieon_cli.util import check_kmc_patch
if not check_kmc_patch('kmc'):
    raise RuntimeError('KMC stdin capability probe failed')
receipt = dict(schema='ashg-etc.pangenome_runtime.v1', status='env_ready',
               cluster='ashg-etc', headnode='i-004609f020b02705a', fsx='fs-0d55fedaeb3ca246b',
               prefix=str(ROOT / 'env'), python=sys.version,
               cli_tag=selected.cli_tag, cli_commit=selected.cli_commit,
               wheel_sha256=digest(ROOT / f'wheels/sentieon_cli-{selected.cli_tag}-py3-none-any.whl'),
               kmc_patched_release='v3.2.4-pipe2', kmc_stdin_capability=True, tools=tools,
               packages={n: importlib.metadata.version(n) for n in ('mappy', 'vcflib', 'Levenshtein', 'packaging')},
               graph_asset_ready=(ROOT / 'evidence/asset_ready.json').is_file(), scientific_validation='pending', production_accepted=False)
(ROOT / 'evidence/env_ready.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('status', 'cli_tag', 'cli_commit', 'wheel_sha256', 'kmc_stdin_capability')}))
