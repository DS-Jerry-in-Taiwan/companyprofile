"""End-to-end runner that orchestrates batch tests, token logging, and hallucination checks."""

from pathlib import Path
import subprocess


def main():
    # run batch test
    subprocess.run(["python", "scripts/batch_test.py", "--limit", "10"], check=True)
    # run hallucination checks
    # simple: compare outputs
    out_dir = Path("outputs/generated_results")
    samples = Path("data/test_samples").glob("*.json")
    for s in samples:
        res = out_dir / (s.stem + ".result.json")
        if res.exists():
            subprocess.run(["python", "scripts/hallucination_checker.py"], check=False)


if __name__ == "__main__":
    main()
