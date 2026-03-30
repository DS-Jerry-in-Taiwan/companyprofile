"""Performance timing helper.

Usage:
  python scripts/perf_timer.py --cmd "python scripts/batch_test.py --limit 5"
"""

import argparse
import time
import subprocess
from contextlib import contextmanager


@contextmanager
def timer(label: str):
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        print(f"[PERF] {label}: {end - start:.3f}s")


def run_command(cmd: str):
    with timer(cmd):
        subprocess.run(cmd, shell=True, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", required=True, help="Command to time")
    args = parser.parse_args()
    run_command(args.cmd)


if __name__ == "__main__":
    main()
