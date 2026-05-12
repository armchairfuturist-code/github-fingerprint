#!/usr/bin/env python3
"""
Worker startup script for the Celery proof generation worker.

Starts a Celery worker that listens on the ``proof_generation`` queue
and processes async proof tasks.

Usage:
    python api/worker.py                          # foreground worker
    python api/worker.py --loglevel=INFO           # explicit log level
    python api/worker.py --concurrency=4           # 4 concurrent tasks

Environment variables:
    REDIS_URL                    Redis connection URL (default: redis://localhost:6379/0)
    CELERY_WORKER_CONCURRENCY    Worker concurrency (default: 2)
    CELERY_LOG_LEVEL             Log level (default: INFO)
"""
import os
import sys

# Ensure the project root is on sys.path so ``api`` package imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.celery_app import celery_app

if __name__ == "__main__":
    # Parse log level from env or default to INFO
    log_level = os.environ.get("CELERY_LOG_LEVEL", "INFO").upper()
    concurrency = os.environ.get(
        "CELERY_WORKER_CONCURRENCY", "2"
    )

    # Build argv for celery worker
    argv = [
        "worker",
        "--loglevel=%s" % log_level,
        "--concurrency=%s" % concurrency,
        "--queues=proof_generation",
        "--hostname=proof-worker@%%h",
        "--without-gossip",       # reduce chatter on single-node
        "--without-mingle",       # skip cluster synchronization
        "--without-heartbeat",    # heartbeat not needed for single broker
    ]

    print("Starting Celery proof worker...")
    print(f"  Concurrency: {concurrency}")
    print(f"  Log level:   {log_level}")
    print(f"  Queues:      proof_generation")
    print()

    celery_app.worker_main(argv)
