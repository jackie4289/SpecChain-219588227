"""Validate that the repository contains the expected deliverables."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRECTORIES = [
    "data",
    "personas",
    "spec",
    "tests",
    "metrics",
    "prompts",
    "reflection",
    "src",
]

REQUIRED_FILES = [
    "data/reviews_raw.jsonl",
    "data/reviews_clean.jsonl",
    "data/dataset_metadata.json",
    "data/review_groups_manual.json",
    "data/review_groups_auto.json",
    "data/review_groups_hybrid.json",
    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",
    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",
    "tests/tests_manual.json",
    "tests/tests_manual.feature",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",
    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",
    "metrics/metrics_summary.json",
    "prompts/prompt_auto.json",
    "README.md",
    "reflection/reflection.md",
    "src/00_validate_repo.py",
    "src/01_collect_or_import.py",
    "src/02_clean.py",
    "src/03_manual_coding_template.py",
    "src/04_personas_manual.py",
    "src/05_personas_auto.py",
    "src/06_spec_generate.py",
    "src/07_tests_generate.py",
    "src/08_metrics.py",
    "src/run_all.py",
]


def main() -> None:
    print("Checking repository structure...")
    missing_items: list[str] = []

    for directory in REQUIRED_DIRECTORIES:
        path = ROOT / directory
        if path.is_dir():
            print(f"{directory}/ found")
        else:
            print(f"{directory}/ MISSING")
            missing_items.append(directory)

    for relative_path in REQUIRED_FILES:
        path = ROOT / relative_path
        if path.is_file():
            print(f"{relative_path} found")
        else:
            print(f"{relative_path} MISSING")
            missing_items.append(relative_path)

    if missing_items:
        print("Repository validation complete: missing required items.")
        sys.exit(1)

    print("Repository validation complete")


if __name__ == "__main__":
    main()
