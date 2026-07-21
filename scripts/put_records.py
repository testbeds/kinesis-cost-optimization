#!/usr/bin/env python3
"""Feed sample JSON records into the Kinesis data stream for cost/capacity testing.

Usage:
    python put_records.py --stream kinesis-cost-optimization-demo --count 1000 --rate 50
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
    parser.add_argument("--count", type=int, default=1000, help="Total records to send")
    parser.add_argument("--rate", type=int, default=50, help="Records per second (approx)")
    parser.add_argument("--batch-size", type=int, default=25, help="Records per put_records call (max 500)")
    args = parser.parse_args()

    client = boto3.client("kinesis", region_name=args.region)

    sent = 0
    start = time.monotonic()
    while sent < args.count:
        batch = min(args.batch_size, args.count - sent)
        entries = [make_record(sent + j) for j in range(batch)]
        response = client.put_records(
            StreamName=args.stream,
            Records=[
                {
                    "Data": json.dumps(r).encode("utf-8"),
                    "PartitionKey": str(r["user_id"]),
                }
                for r in entries
            ],
        )

        if response["FailedRecordCount"]:
            print(f"  warning: {response['FailedRecordCount']} records failed in this batch")

        sent += batch
        elapsed = time.monotonic() - start
        print(f"sent {sent}/{args.count} records ({elapsed:.1f}s elapsed)")

        target_elapsed = sent / args.rate
        sleep_for = target_elapsed - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)

    print(f"done: {sent} records sent in {time.monotonic() - start:.1f}s")


if __name__ == "__main__":
    main()
