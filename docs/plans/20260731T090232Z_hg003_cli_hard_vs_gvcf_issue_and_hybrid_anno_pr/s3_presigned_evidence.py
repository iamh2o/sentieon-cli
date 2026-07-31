#!/usr/bin/env python3
"""Create presigned transfers and verify private S3 evidence objects."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
from pathlib import Path
from typing import Iterator

import boto3


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    expected = {"object_key", "source_path", "size_bytes", "sha256"}
    if not rows:
        raise ValueError(f"{path} is empty")
    if set(rows[0]) != expected:
        raise ValueError(f"{path} has unexpected columns: {sorted(rows[0])}")
    return rows


def client(profile: str, region: str):
    return boto3.Session(
        profile_name=profile,
        region_name=region,
    ).client("s3")


def full_key(prefix: str, object_key: str) -> str:
    return f"{prefix.rstrip('/')}/{object_key}"


def write_private(path: Path, lines: Iterator[str]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as output:
        for line in lines:
            output.write(line)


def create_put_manifest(args: argparse.Namespace) -> int:
    rows = read_manifest(args.manifest)
    s3 = client(args.profile, args.region)
    existing = s3.list_objects_v2(
        Bucket=args.bucket,
        Prefix=f"{args.prefix.rstrip('/')}/",
        MaxKeys=1,
    )
    if existing.get("KeyCount", 0):
        raise RuntimeError(
            f"refusing to overwrite nonempty prefix s3://{args.bucket}/"
            f"{args.prefix.rstrip('/')}/"
        )

    def lines() -> Iterator[str]:
        yield "object_key\tsource_path\tsize_bytes\tsha256\tput_url\n"
        for row in rows:
            key = full_key(args.prefix, row["object_key"])
            url = s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": args.bucket,
                    "Key": key,
                    "Metadata": {"sha256": row["sha256"]},
                },
                ExpiresIn=args.expires,
            )
            yield (
                f"{row['object_key']}\t{row['source_path']}\t"
                f"{row['size_bytes']}\t{row['sha256']}\t{url}\n"
            )

    write_private(args.output, lines())
    print(f"wrote {len(rows)} presigned PUT URLs to {args.output}")
    return 0


def verify(args: argparse.Namespace) -> int:
    rows = read_manifest(args.manifest)
    s3 = client(args.profile, args.region)
    public_access = s3.get_public_access_block(Bucket=args.bucket)[
        "PublicAccessBlockConfiguration"
    ]
    required_blocks = {
        "BlockPublicAcls",
        "IgnorePublicAcls",
        "BlockPublicPolicy",
        "RestrictPublicBuckets",
    }
    if not all(public_access.get(item) for item in required_blocks):
        raise RuntimeError(
            f"bucket public access block is incomplete: {public_access}"
        )

    with args.output.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(
            (
                "object_key",
                "expected_size",
                "observed_size",
                "expected_sha256",
                "observed_sha256",
                "verification",
            )
        )
        failures = 0
        for row in rows:
            key = full_key(args.prefix, row["object_key"])
            observed = s3.head_object(Bucket=args.bucket, Key=key)
            observed_size = str(observed["ContentLength"])
            observed_sha = observed.get("Metadata", {}).get("sha256", "")
            status = "SUCCESS"
            if (
                observed_size != row["size_bytes"]
                or observed_sha != row["sha256"]
            ):
                status = "FAIL"
                failures += 1
            writer.writerow(
                (
                    row["object_key"],
                    row["size_bytes"],
                    observed_size,
                    row["sha256"],
                    observed_sha,
                    status,
                )
            )
    if failures:
        raise RuntimeError(f"{failures} S3 objects failed verification")
    print(
        f"verified {len(rows)} private objects beneath "
        f"s3://{args.bucket}/{args.prefix.rstrip('/')}/"
    )
    return 0


def create_get_urls(args: argparse.Namespace) -> int:
    rows = read_manifest(args.manifest)
    s3 = client(args.profile, args.region)
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        seconds=args.expires
    )
    selected = set(args.object_key)
    if selected:
        unknown = selected.difference(row["object_key"] for row in rows)
        if unknown:
            raise ValueError(f"unknown object keys: {sorted(unknown)}")
        rows = [row for row in rows if row["object_key"] in selected]

    def lines() -> Iterator[str]:
        yield f"expires_utc\t{expires_at.isoformat()}\n"
        yield "object_key\tget_url\n"
        for row in rows:
            url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": args.bucket,
                    "Key": full_key(args.prefix, row["object_key"]),
                },
                ExpiresIn=args.expires,
            )
            yield f"{row['object_key']}\t{url}\n"

    write_private(args.output, lines())
    print(f"wrote {len(rows)} presigned GET URLs to {args.output}")
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--profile", default="lsmc")
    parser.add_argument("--region", default="us-west-2")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    put_parser = subparsers.add_parser("put-manifest")
    add_common(put_parser)
    put_parser.add_argument("--output", required=True, type=Path)
    put_parser.add_argument("--expires", type=int, default=21600)
    put_parser.set_defaults(func=create_put_manifest)

    verify_parser = subparsers.add_parser("verify")
    add_common(verify_parser)
    verify_parser.add_argument("--output", required=True, type=Path)
    verify_parser.set_defaults(func=verify)

    get_parser = subparsers.add_parser("get-urls")
    add_common(get_parser)
    get_parser.add_argument("--output", required=True, type=Path)
    get_parser.add_argument("--expires", type=int, default=604800)
    get_parser.add_argument("--object-key", action="append", default=[])
    get_parser.set_defaults(func=create_get_urls)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
