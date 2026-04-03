"""Generate automated validation tests from requirements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from automation_utils import (
    MODEL_NAME,
    TEST_PROMPT_TEMPLATE,
    extract_json_payload,
    fallback_tests_for_requirement,
    get_groq_api_key,
    groq_chat,
    merge_prompt_file,
    parse_requirements,
    require_groq_or_fallback,
    write_json,
)

DEFAULT_SPEC = Path("spec/spec_auto.md")
DEFAULT_OUTPUT = Path("tests/tests_auto.json")
DEFAULT_PROMPT_OUTPUT = Path("prompts/prompt_auto.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate automated validation tests from requirements.")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prompt-output", type=Path, default=DEFAULT_PROMPT_OUTPUT)
    parser.add_argument("--api-key", default=None, help="Optional Groq API key override")
    return parser.parse_args()


def generate_tests_for_requirement(
    requirement: dict[str, str],
    *,
    api_key: str | None,
) -> list[dict[str, object]]:
    require_groq_or_fallback(api_key, False)

    requirement_summary = {
        "id": requirement["id"],
        "description": requirement["description"],
        "source_persona": requirement["source_persona"],
        "traceability": requirement["traceability"],
        "acceptance_criteria": requirement["acceptance_criteria"],
    }
    messages = [
        {"role": "system", "content": "You are a QA analyst. Return JSON only."},
        {"role": "user", "content": TEST_PROMPT_TEMPLATE.format(requirement_summary=json.dumps(requirement_summary, ensure_ascii=False))},
    ]
    response_text = groq_chat(messages, api_key=api_key)
    payload = extract_json_payload(response_text)
    if not isinstance(payload, dict) or not isinstance(payload.get("tests"), list):
        raise ValueError("Expected a JSON object with a tests list.")

    generated: list[dict[str, object]] = []
    for item in payload["tests"][:2]:
        if not isinstance(item, dict):
            continue
        scenario = str(item.get("scenario", "")).strip()
        steps = item.get("steps")
        expected_result = str(item.get("expected_result", "")).strip()
        if scenario and isinstance(steps, list) and expected_result:
            cleaned_steps = [str(step).strip() for step in steps if str(step).strip()]
            if cleaned_steps:
                generated.append(
                    {
                        "scenario": scenario,
                        "steps": cleaned_steps,
                        "expected_result": expected_result,
                    }
                )

    if len(generated) < 2:
        fallback = fallback_tests_for_requirement(requirement)
        generated.extend(fallback[len(generated) : 2])

    return generated[:2]


def main() -> None:
    args = parse_args()
    api_key = get_groq_api_key(args.api_key)
    require_groq_or_fallback(api_key, False)

    requirements = parse_requirements(args.spec.read_text(encoding="utf-8"))
    if not requirements:
        raise RuntimeError(f"No requirements parsed from {args.spec}")

    tests: list[dict[str, object]] = []
    test_index = 1
    for requirement in requirements:
        generated_tests = generate_tests_for_requirement(
            requirement,
            api_key=api_key,
        )
        for item in generated_tests:
            tests.append(
                {
                    "test_id": f"T_auto_{test_index}",
                    "requirement_id": requirement["id"],
                    "scenario": item["scenario"],
                    "steps": item["steps"],
                    "expected_result": item["expected_result"],
                }
            )
            test_index += 1

    write_json(args.output, {"tests": tests})
    merge_prompt_file(
        args.prompt_output,
        {
            "model": MODEL_NAME,
            "test_generation_prompt_template": TEST_PROMPT_TEMPLATE,
        },
    )

    print(f"Wrote automated tests to {args.output}")


if __name__ == "__main__":
    main()
