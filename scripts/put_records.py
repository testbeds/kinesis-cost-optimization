#!/usr/bin/env python3
"""Feed sample JSON records into the Kinesis data stream for cost/capacity testing.

Defaults are sized to approach a single shard's limits (1000 records/sec,
1MB/sec) so you can see throttling / compare PROVISIONED vs ON_DEMAND.

Usage:
    python put_records.py --stream kinesis-cost-optimization-demo --count 200000 --rate 3000
"""
import argparse
import json
import random
import time
import uuid
from datetime import datetime, timezone

import boto3


def make_record(i: int) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "sequence": i,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": random.randint(1, 10_000),
        "event_type": random.choice(["click", "view", "purchase", "signup"]),
        "value": round(random.uniform(1, 500), 2),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", required=True, help="Kinesis stream name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--count", type=int, default=200_000, help="Total records to send")
    parser.add_argument("--rate", type=int, default=3000, help="Target records per second (aggregate)")
    parser.add_argument("--batch-size", type=int, default=500, help="Records per put_records call (AWS max 500)")
    args = parser.parse_args()

    client = boto3.client("kinesis", region_name=args.region)

    sent = 0
    bytes_sent = 0
    start = time.monotonic()
    while sent < args.count:
        batch = min(args.batch_size, args.count - sent)
        entries = [make_record(sent + j) for j in range(batch)]
        payloads = [json.dumps(r).encode("utf-8") for r in entries]
        response = client.put_records(
            StreamName=args.stream,
            Records=[
                {"Data": data, "PartitionKey": str(r["user_id"])}
                for data, r in zip(payloads, entries)
            ],
        )

        if response["FailedRecordCount"]:
            print(f"  warning: {response['FailedRecordCount']} records failed in this batch")

        sent += batch
        bytes_sent += sum(len(p) for p in payloads)
        elapsed = time.monotonic() - start
        actual_rate = sent / elapsed if elapsed > 0 else 0
        print(
            f"sent {sent}/{args.count} records ({elapsed:.1f}s elapsed, "
            f"{actual_rate:.0f} rec/s, {bytes_sent / elapsed / 1024:.0f} KB/s)"
        )

        target_elapsed = sent / args.rate
        sleep_for = target_elapsed - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)

    elapsed = time.monotonic() - start
    print(
        f"done: {sent} records ({bytes_sent / 1024:.0f} KB) sent in {elapsed:.1f}s "
        f"(avg {sent / elapsed:.0f} rec/s, {bytes_sent / elapsed / 1024:.0f} KB/s)"
    )


if __name__ == "__main__":
    main()
