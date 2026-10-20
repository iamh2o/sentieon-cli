"""Acquire only the three approved immutable assets on ashg-etc.

No reference filesystem writes, destination overwrites or alternative assets.
Each exact shared S3 key must be absent or already carry the same observed
content digest. The hashes certify this transfer, not a vendor-signed manifest.
"""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path('/fsx/work/pangenome_runtime/20261020')
BUCKET = 'lsmc-dayoa-references-usw2'
ASSETS = [
    ('HybridPangenomeIlluminaONT1.0.bundle', 511706146,
     'https://s3.amazonaws.com/sentieon-release/other/HybridPangenomeIlluminaONT1.0.bundle',
     'runtime_assets/cached_envs/sentieon-genomics-202503.04/bundles/HybridPangenomeIlluminaONT1.0.bundle'),
    ('hprc-v2.1-mc-grch38.gbz', 5492627216,
     'https://s3-us-west-2.amazonaws.com/human-pangenomics/pangenomes/freeze/release2/minigraph-cactus/v2.1/hprc-v2.1-mc-grch38/hprc-v2.1-mc-grch38.gbz',
     'genomic_data/organism_references/H_sapiens/panhg38/hprc-v2.1-mc-grch38.gbz'),
    ('hprc-v2.1-mc-grch38.hapl', 21376720088,
     'https://s3-us-west-2.amazonaws.com/human-pangenomics/pangenomes/freeze/release2/minigraph-cactus/v2.1/hprc-v2.1-mc-grch38/hprc-v2.1-mc-grch38.hapl',
     'genomic_data/organism_references/H_sapiens/panhg38/hprc-v2.1-mc-grch38.hapl'),
]

def aws(*args):
    return subprocess.run(['aws', '--no-cli-pager', *args], text=True, capture_output=True)

def head(key):
    proc = aws('s3api', 'head-object', '--region', 'us-west-2', '--bucket', BUCKET, '--key', key)
    if proc.returncode == 0:
        return json.loads(proc.stdout)
    if '(404)' in proc.stderr or '(NoSuchKey)' in proc.stderr:
        return None
    raise RuntimeError(proc.stderr)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def stage(item):
    name, expected, source_url, key = item
    path = ROOT / 'assets' / name
    before = head(key)
    if path.exists():
        raise FileExistsError(f'Explicit fresh staging required: {path}')
    temporary = path.with_suffix(path.suffix + '.download')
    with urllib.request.urlopen(source_url, timeout=120) as source:
        headers = dict(source.headers)
        if int(source.headers['Content-Length']) != expected:
            raise ValueError(f'Unexpected vendor byte count for {name}')
        h = hashlib.sha256()
        count = 0
        with temporary.open('xb') as target:
            while chunk := source.read(8 * 1024 * 1024):
                count += len(chunk)
                h.update(chunk)
                target.write(chunk)
        if count != expected:
            raise ValueError(f'Incomplete download {name}: {count} != {expected}')
        sha256 = h.hexdigest()
    temporary.rename(path)
    if before is not None:
        if before['ContentLength'] != expected or before.get('Metadata', {}).get('sha256') != sha256:
            raise RuntimeError(f'Existing shared object does not match staged asset: {key}')
        publication = 'already_identical'
    else:
        # Recheck immediately before publication; never deliberately overwrite.
        if head(key) is not None:
            raise RuntimeError(f'Shared object appeared during acquisition: {key}')
        proc = aws('s3', 'cp', str(path), f's3://{BUCKET}/{key}', '--region', 'us-west-2',
                   '--only-show-errors', '--metadata', f'sha256={sha256}')
        if proc.returncode:
            raise RuntimeError(proc.stderr)
        publication = 'published'
    observed = head(key)
    if observed['ContentLength'] != expected or observed.get('Metadata', {}).get('sha256') != sha256:
        raise RuntimeError(f'Shared object readback mismatch: {key}')
    receipt = dict(name=name, path=str(path), expected_bytes=expected,
                   observed_bytes=count, sha256=sha256, source=source_url,
                   source_headers=headers, destination=f's3://{BUCKET}/{key}',
                   publication=publication, s3_etag=observed['ETag'],
                   s3_version_id=observed.get('VersionId'),
                   completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (ROOT / 'evidence' / f'{name}.transfer.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('name', 'observed_bytes', 'sha256', 'publication')}), flush=True)
    return receipt

ROOT.joinpath('assets').mkdir(parents=True, exist_ok=True)
ROOT.joinpath('evidence').mkdir(exist_ok=True)
identity = aws('sts', 'get-caller-identity')
identity.check_returncode()
identity = json.loads(identity.stdout)
if identity['Account'] != '108782052779' or not identity['Arn'].endswith('/i-004609f020b02705a'):
    raise RuntimeError('Wrong headnode identity')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    receipts = list(executor.map(stage, ASSETS))
(ROOT / 'evidence' / 'asset_transfers.json').write_text(json.dumps(receipts, indent=2) + '\n')
print('ASSET_STAGING_COMPLETE', flush=True)
