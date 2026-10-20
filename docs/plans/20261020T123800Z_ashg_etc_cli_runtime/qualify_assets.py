"""Hash the exact completed downloads and check native graph/model metadata."""
import ast
import dataclasses
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

from sentieon_cli.archive import ar_load
from sentieon_cli.pangenome_meta import detect_pangenome_reference, read_hapl_header
from sentieon_cli.ultima_pangenome import ULTIMA_MAPPER_SHA256, LONGREADSV_SHA256, POPULATION_ID

ROOT = Path('/fsx/work/pangenome_runtime/20261020')
REFERENCE_ROOT = Path('/fsx/references/genomic_data/organism_references/H_sapiens/panhg38')
DRIVER_ROOT = Path('/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.04')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for data in iter(lambda: source.read(8 * 1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

tree = ast.parse((ROOT / 'stage_assets.py').read_text())
assets = next(ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ASSETS' for t in node.targets))
inventory = []
for name, expected_bytes, source, key in assets:
    path = ROOT / 'assets' / name
    if path.stat().st_size != expected_bytes:
        raise ValueError(f'Incomplete staged asset: {name}')
    headers = urllib.request.urlopen(urllib.request.Request(source, method='HEAD'), timeout=60).headers
    if int(headers['Content-Length']) != expected_bytes:
        raise ValueError('Vendor source size changed')
    inventory.append(dict(name=name, path=str(path), observed_bytes=expected_bytes,
                          sha256=digest(path), source=source,
                          source_etag=headers.get('ETag'), source_last_modified=headers.get('Last-Modified'),
                          destination=f's3://lsmc-dayoa-references-usw2/{key}'))
    print(json.dumps({k: inventory[-1][k] for k in ('name', 'observed_bytes', 'sha256')}), flush=True)
(ROOT / 'evidence/asset_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
graph = detect_pangenome_reference(ROOT / 'assets/hprc-v2.1-mc-grch38.gbz')
hapl = read_hapl_header(ROOT / 'assets/hprc-v2.1-mc-grch38.hapl')
if graph.ref_name != 'GRCh38' or graph.contig_prefix != 'GRCh38#0#' or hapl.k != 29 or hapl.top_level_chains <= 0:
    raise ValueError('Incompatible graph and HAPL metadata')
bundles = []
roles = {}
for bundle, names in (
    (ROOT / 'assets/HybridPangenomeIlluminaONT1.0.bundle', ('dnascope.model', 'extract.model', 'longreadsv.model')),
    (DRIVER_ROOT / 'bundles/SentieonUltimaPangenomeRealignWGS1.3.bundle', ('minimap2.model',)),
):
    info = json.loads(ar_load(str(bundle / 'bundle_info.json')))
    bundles.append(dict(path=str(bundle), sha256=digest(bundle), vendor_metadata=info))
    for name in names:
        payload = ar_load(str(bundle / name))
        sha256 = hashlib.sha256(payload).hexdigest()
        expected = {'minimap2.model': ULTIMA_MAPPER_SHA256, 'longreadsv.model': LONGREADSV_SHA256}.get(name)
        if expected and sha256 != expected:
            raise ValueError(f'Unexpected vendor member: {name}')
        roles[name] = dict(path=str(bundle / name), bytes=len(payload), sha256=sha256)
assert bundles[0]['vendor_metadata']['SentieonVcfID'] == POPULATION_ID
population = REFERENCE_ROOT / 'pop-v20-20260528.vcf.gz'
header = subprocess.check_output([str(ROOT / 'env/bin/bcftools'), 'view', '-h', str(population)], timeout=180).decode()
if f'##SentieonVcfID={POPULATION_ID}' not in header:
    raise ValueError('Population VCF identity mismatch')
receipt = dict(schema='ashg-etc.pangenome_assets.v1', status='asset_ready',
               cluster='ashg-etc', headnode='i-004609f020b02705a', fsx='fs-0d55fedaeb3ca246b',
               inventory=inventory, graph_metadata=dataclasses.asdict(graph),
               haplotype_metadata=dataclasses.asdict(hapl), bundles=bundles, models=roles,
               reference=str(REFERENCE_ROOT / 'hg38_ucsc.fa'),
               reference_fai_sha256=digest(REFERENCE_ROOT / 'hg38_ucsc.fa.fai'),
               population_vcf=str(population), population_id=POPULATION_ID,
               population_header_sha256=hashlib.sha256(header.encode()).hexdigest(),
               population_index=str(population) + '.tbi',
               observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               scientific_validation='pending', production_accepted=False,
               checksum_authority='Observed transfer hashes; no vendor-signed GBZ/HAPL checksum manifest supplied')
(ROOT / 'evidence/asset_ready.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('ASSET_READY', flush=True)
