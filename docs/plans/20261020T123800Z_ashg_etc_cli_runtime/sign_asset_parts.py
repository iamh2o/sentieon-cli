"""Use approved lsmc operator credentials to sign exact asset upload parts.

Run on the laptop only for request signing; no asset bytes cross the laptop.
The manifest contains credentials and is chmod 0600 outside the repository.
Never print that manifest, signed URLs, or credential material.
"""
import argparse
import datetime
import json
import math
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

p = argparse.ArgumentParser()
p.add_argument('inventory')
p.add_argument('secret_manifest')
a = p.parse_args()
inventory = json.loads(Path(a.inventory).read_text())
session = boto3.Session(profile_name='lsmc', region_name='us-west-2')
if session.client('sts').get_caller_identity()['Account'] != '108782052779':
    raise RuntimeError('Wrong operator account')
client = session.client('s3')
assets = []
for item in inventory:
    bucket, key = item['destination'].removeprefix('s3://').split('/', 1)
    if bucket != 'lsmc-dayoa-references-usw2':
        raise RuntimeError('Unexpected asset bucket')
    try:
        client.head_object(Bucket=bucket, Key=key)
    except ClientError as error:
        if error.response['Error']['Code'] not in ('404', 'NoSuchKey', 'NotFound'):
            raise
    else:
        raise RuntimeError('Destination exists; explicit reconciliation required')
    upload = client.create_multipart_upload(Bucket=bucket, Key=key,
                                             Metadata={'sha256': item['sha256']})
    part_bytes = 128 * 1024 * 1024
    part_count = math.ceil(item['observed_bytes'] / part_bytes)
    parts = []
    for number in range(1, part_count + 1):
        url = client.generate_presigned_url('upload_part', Params={
            'Bucket': bucket, 'Key': key, 'UploadId': upload['UploadId'],
            'PartNumber': number}, ExpiresIn=3600, HttpMethod='PUT')
        parts.append({'number': number, 'url': url})
    assets.append(dict(item, bucket=bucket, key=key,
                       upload_id=upload['UploadId'], part_bytes=part_bytes, parts=parts))
manifest = {'schema': 'ashg-etc.approved_asset_multipart.v1',
            'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'expires_seconds': 3600, 'assets': assets}
fd = os.open(a.secret_manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as target:
    json.dump(manifest, target)
print(json.dumps({'status': 'signed', 'assets': len(assets),
                  'parts': sum(len(x['parts']) for x in assets)}))
