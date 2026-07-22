#!/usr/bin/env python3
"""Feed sample JSON records into the Kinesis data stream for cost/capacity testing.

Defaults are sized to approach a single shard's limits (1000 records/sec,
1MB/sec) so you can see throttling / compare PROVISIONED vs ON_DEMAND.
PutRecords calls run concurrently (--workers) since a single thread is
bound by per-call network round-trip latency.

Usage:
    python put_records.py --stream kinesis-cost-optimization-demo --count 200000 --rate 5000 --workers 10
"""
import argparse
import json
import random
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
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


def send_batch(client, stream_name, entries):
    response = client.put_records(
        StreamName=stream_name,
        Records=[
            {
                "Data": json.dumps(r).encode("utf-8"),
                "PartitionKey": str(r["user_id"]),
            }
            for r in entries
        ],
    )
    return response["FailedRecordCount"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", required=True, help="Kinesis stream name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--count", type=int, default=200000, help="Total records to send")
    parser.add_argument("--rate", type=int, default=5000, help="Target records per second (aggregate)")
    parser.add_argument("--batch-size", type=int, default=500, help="Records per put_records call (AWS max 500)")
    parser.add_argument("--workers", type=int, default=10, help="Concurrent put_records calls in flight")
    args = parser.parse_args()

    client = boto3.client("kinesis", region_name=args.region)

    sent = 0
    failed = 0
    start = time.monotonic()
    in_flight = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        while sent < args.count:
            if len(in_flight) >= args.workers:
                done, not_done = wait(in_flight, return_when=FIRST_COMPLETED)
                for f in done:
                    failed += f.result()
                in_flight = list(not_done)

            batch = min(args.batch_size, args.count - sent)
            entries = [make_record(sent + j) for j in range(batch)]
            in_flight.append(pool.submit(send_batch, client, args.stream, entries))
            sent += batch

            elapsed = time.monotonic() - start
            print(f"submitted {sent}/{args.count} records ({elapsed:.1f}s elapsed, {len(in_flight)} in flight)")

            target_elapsed = sent / args.rate
            sleep_for = target_elapsed - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

        for f in in_flight:
            failed += f.result()

    elapsed = time.monotonic() - start
    if failed:
        print(f"warning: {failed} records failed across the run")
    print(f"done: {sent} records sent in {elapsed:.1f}s (avg {sent / elapsed:.0f} rec/s)")


if __name__ == "__main__":
    main()
