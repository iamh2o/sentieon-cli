"""Upload approved exact multipart bytes from ashg-etc without IAM mutation.

Input is a private operator-signed URL manifest. Output includes only native
paths, exact object keys, bytes, observed hashes and S3 part ETags; no URLs.
"""
import concurrent.futures
import json
from pathlib import Path
import sys
import urllib.request

manifest = json.loads(Path(sys.argv[1]).read_text())
receipt_path = Path(sys.argv[2])
if manifest['schema'] != 'ashg-etc.approved_asset_multipart.v1':
    raise RuntimeError('Wrong manifest schema')
results = []
for asset in manifest['assets']:
    path = Path(asset['path'])
    if path.stat().st_size != asset['observed_bytes']:
        raise ValueError('Staged asset size changed')
    def upload(part):
        offset = (part['number'] - 1) * asset['part_bytes']
        with path.open('rb') as source:
            source.seek(offset)
            data = source.read(asset['part_bytes'])
        request = urllib.request.Request(part['url'], data=data, method='PUT')
        with urllib.request.urlopen(request, timeout=240) as response:
            if response.status != 200:
                raise RuntimeError('Multipart part failed')
            return {'PartNumber': part['number'], 'ETag': response.headers['ETag']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        parts = list(executor.map(upload, asset['parts']))
    result = {key: asset[key] for key in ('name', 'path', 'destination', 'observed_bytes',
                                         'sha256', 'bucket', 'key', 'upload_id')}
    result['parts'] = sorted(parts, key=lambda item: item['PartNumber'])
    results.append(result)
    receipt_path.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({'name': asset['name'], 'status': 'parts_uploaded',
                      'parts': len(parts)}), flush=True)
print('PRESIGNED_PART_UPLOADS_COMPLETE', flush=True)
