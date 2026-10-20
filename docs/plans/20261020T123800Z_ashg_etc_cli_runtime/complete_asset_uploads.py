"""Complete only the approved exact multipart assets and verify readback."""
import datetime
import json
from pathlib import Path
import sys

import boto3
from botocore.exceptions import ClientError

session = boto3.Session(profile_name='lsmc', region_name='us-west-2')
if session.client('sts').get_caller_identity()['Account'] != '108782052779':
    raise RuntimeError('Wrong operator account')
client = session.client('s3')
receipts = []
for item in json.loads(Path(sys.argv[1]).read_text()):
    try:
        client.head_object(Bucket=item['bucket'], Key=item['key'])
    except ClientError as error:
        if error.response['Error']['Code'] not in ('404', 'NoSuchKey', 'NotFound'):
            raise
    else:
        raise RuntimeError('Destination appeared before completion; do not overwrite')
    result = client.complete_multipart_upload(
        Bucket=item['bucket'], Key=item['key'], UploadId=item['upload_id'],
        MultipartUpload={'Parts': item['parts']})
    observed = client.head_object(Bucket=item['bucket'], Key=item['key'])
    if observed['ContentLength'] != item['observed_bytes']:
        raise ValueError('Published object size mismatch')
    if observed.get('Metadata', {}).get('sha256') != item['sha256']:
        raise ValueError('Published object digest metadata mismatch')
    receipts.append({key: item[key] for key in ('name', 'path', 'destination',
                                                'observed_bytes', 'sha256')})
    receipts[-1].update(s3_etag=observed['ETag'], s3_version_id=observed.get('VersionId'),
                         completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                         method='operator_signed_multipart_from_ashg_etc')
Path(sys.argv[2]).write_text(json.dumps(receipts, indent=2) + '\n')
print(json.dumps({'status': 'published_and_readback_verified', 'assets': len(receipts)}))
