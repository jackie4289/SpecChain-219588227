"""Compute flat metrics for one pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from automation_utils import (
    compute_ambiguity_ratio,
    compute_traceability_links,
    parse_requirements,
    read_json,
    write_json,
)

ROOT = Path(__file__).resolve().parent.parent

PIPELINE_MAP = {
    "manual": {"suffix": "manual", "name": "manual"},
    "auto": {"suffix": "auto", "name": "automated"},
    "automated": {"suffix": "auto", "name": "automated"},
    "hybrid": {"suffix": "hybrid", "name": "hybrid"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute metrics for one pipeline.")
    parser.add_argument("--pipeline", default="auto", choices=sorted(PIPELINE_MAP))
    parser.add_argument("--reviews", type=Path, default=ROOT / "data" / "reviews_clean.jsonl")
    return parser.parse_args()


def count_clean_reviews(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def update_metrics_summary() -> None:
    summary_path = ROOT / "metrics" / "metrics_summary.json"
    summary: dict[str, object] = {}
    for key, info in (("manual", PIPELINE_MAP["manual"]), ("automated", PIPELINE_MAP["automated"]), ("hybrid", PIPELINE_MAP["hybrid"])):
        path = ROOT / "metrics" / f"metrics_{info['suffix']}.json"
        if path.exists() and path.stat().st_size > 0:
            summary[key] = read_json(path, {})
    if summary:
        write_json(summary_path, summary)


def main() -> None:
    args = parse_args()
    pipeline_info = PIPELINE_MAP[args.pipeline]
    suffix = pipeline_info["suffix"]

    review_groups_path = ROOT / "data" / f"review_groups_{suffix}.json"
    personas_path = ROOT / "personas" / f"personas_{suffix}.json"
    spec_path = ROOT / "spec" / f"spec_{suffix}.md"
    tests_path = ROOT / "tests" / f"tests_{suffix}.json"
    metrics_path = ROOT / "metrics" / f"metrics_{suffix}.json"

    review_groups = read_json(review_groups_path, {"groups": []})
    personas = read_json(personas_path, {"personas": []})
    tests = read_json(tests_path, {"tests": []})
    requirements = parse_requirements(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else []

    dataset_size = count_clean_reviews(args.reviews)
    persona_count = len(personas.get("personas", []))
    requirements_count = len(requirements)
    tests_count = len(tests.get("tests", []))

    covered_review_ids = {
        review_id
        for group in review_groups.get("groups", [])
        for review_id in group.get("review_ids", [])
    }
    review_coverage = round(len(covered_review_ids) / dataset_size, 4) if dataset_size else 0.0

    traceable_requirements = sum(1 for requirement in requirements if requirement.get("source_persona"))
    traceability_ratio = round(traceable_requirements / requirements_count, 4) if requirements_count else 0.0

    tested_requirement_ids = {
        test.get("requirement_id")
        for test in tests.get("tests", [])
        if test.get("requirement_id")
    }
    testability_rate = round(
        sum(1 for requirement in requirements if requirement["id"] in tested_requirement_ids) / requirements_count,
        4,
    ) if requirements_count else 0.0

    metrics = {
        "pipeline": pipeline_info["name"],
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": compute_traceability_links(review_groups, personas, requirements, tests),
        "review_coverage": review_coverage,
        "traceability_ratio": traceability_ratio,
        "testability_rate": testability_rate,
        "ambiguity_ratio": compute_ambiguity_ratio(requirements),
    }
    write_json(metrics_path, metrics)
    update_metrics_summary()

    print(f"Wrote metrics to {metrics_path}")


if __name__ == "__main__":
    main()
