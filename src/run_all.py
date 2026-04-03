"""Run the automated pipeline end to end.

This script automates the programmatic part of the repository workflow:
1. Clean the raw review dataset.
2. Generate automated review groups and personas.
3. Generate an automated specification from those personas.
4. Generate automated validation tests from that specification.
5. Compute automated metrics and refresh the summary file.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from automation_utils import get_groq_api_key

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the automated pipeline end to end.")
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip rerunning src/02_clean.py",
    )
    return parser.parse_args()


def run_step(script_name: str, extra_args: list[str]) -> None:
    command = [sys.executable, str(ROOT / "src" / script_name), *extra_args]
    subprocess.run(command, check=True, cwd=ROOT)


def main() -> None:
    args = parse_args()
    api_key = get_groq_api_key()
    shared_args: list[str] = []
    if not api_key:
        raise RuntimeError("Groq API key is not available for the automated pipeline.")

    # Step 1: Clean the raw review dataset and write `data/reviews_clean.jsonl`
    # plus the dataset metadata file used by later pipeline stages.
    if not args.skip_clean:
        run_step("02_clean.py", [])

    # Step 2: Read the cleaned reviews and produce:
    # - `data/review_groups_auto.json`
    # - `personas/personas_auto.json`
    # - `prompts/prompt_auto.json`
    run_step("05_personas_auto.py", shared_args)

    # Step 3: Read the automated personas and produce `spec/spec_auto.md`.
    run_step("06_spec_generate.py", shared_args)

    # Step 4: Read the automated specification and produce `tests/tests_auto.json`.
    run_step("07_tests_generate.py", shared_args)

    # Step 5: Compute automated metrics and refresh `metrics/metrics_summary.json`.
    run_step("08_metrics.py", ["--pipeline", "auto"])

    print("Automated pipeline completed.")


if __name__ == "__main__":
    main()
