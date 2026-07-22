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


def make_record(i: int, partition_keys: int = 10_000) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "sequence": i,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": random.randint(1, partition_keys),
        "event_type": random.choice(["click", "view", "purchase", "signup"]),
        "value": round(random.uniform(1, 500), 2),
    }


def send_batch(client, stream_name, entries, max_retries=5, base_delay=0.5, max_delay=10.0):
    """Send a batch via put_records, retrying only the records that failed
    (e.g. ProvisionedThroughputExceededException) with exponential backoff
    and jitter. Returns the count of records that were still failing after
    exhausting retries (i.e. actually lost).
    """
    pending = entries
    attempt = 0
    while pending:
        response = client.put_records(
            StreamName=stream_name,
            Records=[
                {
                    "Data": json.dumps(r).encode("utf-8"),
                    "PartitionKey": str(r["user_id"]),
                }
                for r in pending
            ],
        )

        if response["FailedRecordCount"] == 0:
            return 0

        pending = [r for r, result in zip(pending, response["Records"]) if "ErrorCode" in result]

        if attempt >= max_retries:
            return len(pending)

        delay = min(base_delay * (2**attempt) + random.uniform(0, base_delay), max_delay)
        time.sleep(delay)
        attempt += 1

    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", required=True, help="Kinesis stream name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--count", type=int, default=200000, help="Total records to send")
    parser.add_argument("--rate", type=int, default=5000, help="Target records per second (aggregate)")
    parser.add_argument("--batch-size", type=int, default=500, help="Records per put_records call (AWS max 500)")
    parser.add_argument("--workers", type=int, default=10, help="Concurrent put_records calls in flight")
    parser.add_argument("--max-retries", type=int, default=5, help="Retries per record before giving up (exponential backoff)")
    parser.add_argument(
        "--partition-keys",
        type=int,
        default=10_000,
        help="Distinct partition key values used (user_id range). Set low (e.g. 1) to concentrate "
        "load onto a single shard and trigger throttling deliberately.",
    )
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
            entries = [make_record(sent + j, args.partition_keys) for j in range(batch)]
            in_flight.append(pool.submit(send_batch, client, args.stream, entries, args.max_retries))
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
        print(f"warning: {failed} records permanently lost after exhausting {args.max_retries} retries each")
    print(
        f"done: {sent - failed}/{sent} records durably written in {elapsed:.1f}s "
        f"(avg {sent / elapsed:.0f} rec/s)"
    )


if __name__ == "__main__":
    main()
