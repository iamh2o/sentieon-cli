"""Compare actual extracted graph-backbone sequence identities, never bases."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path('/fsx/work/pangenome_runtime/20261020')
INSPECTION = Path('/fsx/work/pangenome_inputs/20261020/inspection')

def dictionary(path):
    result = {}
    for line in path.read_text().splitlines():
        if line.startswith('@SQ\t'):
            fields = dict(field.split(':', 1) for field in line.split('\t')[1:])
            name = fields['SN']
            if name in result or not fields.get('M5'):
                raise ValueError('Missing M5 or duplicate dictionary sequence')
            result[name] = {'length': int(fields['LN']), 'M5': fields['M5']}
    return result

graph_dict_path = ROOT / 'evidence/graph_GRCh38_backbone.dict'
raw = dictionary(graph_dict_path)
prefix = 'GRCh38#0#'
if len(raw) != 195 or any(not key.startswith(prefix) for key in raw):
    raise ValueError('Unexpected extracted reference-path identity')
graph = {key.removeprefix(prefix): value for key, value in raw.items()}
comparisons = {}
for label, filename in (
    ('bjuice', 'bjuice_reference.dict'), ('vendor_ucsc', 'target_reference.dict'),
    ('ont_source', 'ont_source.header.sam'), ('ultima_source', 'ultima_source.header.sam'),
):
    path = INSPECTION / filename
    other = dictionary(path)
    common = set(graph) & set(other)
    differences = {key: {'graph': graph[key], label: other[key]} for key in sorted(common)
                   if graph[key] != other[key]}
    comparisons[label] = dict(path=str(path), total_sequences=len(other), shared=len(common),
                              identical=len(common) - len(differences), differences=differences,
                              missing_from_comparison=sorted(set(graph) - set(other)),
                              extra_in_comparison=sorted(set(other) - set(graph)))
receipt = dict(schema='ashg-etc.graph_backbone_sequence_comparison.v1',
               observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               cluster='ashg-etc', headnode='i-004609f020b02705a',
               graph=str(ROOT / 'assets/hprc-v2.1-mc-grch38.gbz'),
               graph_sha256='11d6047f79575ffb83757462484bad134ed20928bd2c8171ec52e35a54976e2b',
               extraction_command=[str(ROOT / 'env/bin/vg'), 'paths', '-x',
                    str(ROOT / 'assets/hprc-v2.1-mc-grch38.gbz'), '-S', 'GRCh38', '-F'],
               extracted_fasta=str(ROOT / 'evidence/graph_GRCh38_backbone.fa'),
               extracted_dictionary=str(graph_dict_path), name_normalization=f'remove exact {prefix} prefix for comparison only',
               dictionary_sha256=hashlib.sha256(graph_dict_path.read_bytes()).hexdigest(),
               graph_sequence_count=len(graph), graph_sequences=graph, comparisons=comparisons,
               selection_applied=False)
destination = ROOT / 'evidence/graph_reference_sequence_comparison.json'
destination.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({key: {name: result[name] for name in ('total_sequences', 'shared', 'identical')}
                  for key, result in comparisons.items()}))
