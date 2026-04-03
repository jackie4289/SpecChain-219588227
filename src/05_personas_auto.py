"""Automatically group reviews and generate personas."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

from automation_utils import (
    GROUPING_PROMPT_TEMPLATE,
    MODEL_NAME,
    THEME_CONFIGS,
    assign_reviews_to_themes,
    build_cluster_summary,
    extract_json_payload,
    get_groq_api_key,
    groq_chat,
    load_reviews,
    merge_prompt_file,
    normalize_items,
    require_groq_or_fallback,
    write_json,
)

DEFAULT_INPUT = Path("data/reviews_clean.jsonl")
DEFAULT_GROUPS_OUTPUT = Path("data/review_groups_auto.json")
DEFAULT_PERSONAS_OUTPUT = Path("personas/personas_auto.json")
DEFAULT_PROMPT_OUTPUT = Path("prompts/prompt_auto.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automatically group reviews and generate personas.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--groups-output", type=Path, default=DEFAULT_GROUPS_OUTPUT)
    parser.add_argument("--personas-output", type=Path, default=DEFAULT_PERSONAS_OUTPUT)
    parser.add_argument("--prompt-output", type=Path, default=DEFAULT_PROMPT_OUTPUT)
    parser.add_argument("--api-key", default=None, help="Optional Groq API key override")
    return parser.parse_args()


def normalize_scalar_field(value: object, fallback: str) -> str:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return fallback
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                return fallback
            if isinstance(parsed, list):
                return fallback
        return text
    return fallback


def generate_cluster_payload(
    cluster: dict[str, object],
    cluster_summary: dict[str, object],
    *,
    api_key: str | None,
) -> dict[str, object]:
    require_groq_or_fallback(api_key, False)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a requirements analyst working from clustered app reviews. "
                "Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": GROUPING_PROMPT_TEMPLATE.format(cluster_summary=json.dumps(cluster_summary, ensure_ascii=False)),
        },
    ]
    response_text = groq_chat(messages, api_key=api_key)
    payload = extract_json_payload(response_text)
    if not isinstance(payload, dict):
        raise ValueError("Expected an object from the grouping/persona prompt.")
    return payload


def main() -> None:
    args = parse_args()
    api_key = get_groq_api_key(args.api_key)
    require_groq_or_fallback(api_key, False)

    reviews = load_reviews(args.input)
    clustered = assign_reviews_to_themes(reviews)

    groups_output: list[dict[str, object]] = []
    personas_output: list[dict[str, object]] = []

    for index, config in enumerate(THEME_CONFIGS, start=1):
        cluster = clustered[config.key]
        cluster_summary = build_cluster_summary(cluster, reviews)
        payload = generate_cluster_payload(
            cluster,
            cluster_summary,
            api_key=api_key,
        )

        ranked_indexes = cluster["review_indexes"]
        review_ids = [reviews[review_index]["review_id"] for review_index in ranked_indexes]
        example_reviews = [reviews[review_index]["content_original"] for review_index in ranked_indexes[:2]]
        evidence_reviews = review_ids[:3]

        groups_output.append(
            {
                "group_id": config.group_id,
                "theme": normalize_scalar_field(payload.get("theme"), config.default_theme),
                "review_ids": review_ids,
                "example_reviews": example_reviews,
            }
        )

        personas_output.append(
            {
                "id": f"P_auto_{index}",
                "name": normalize_scalar_field(payload.get("persona_name"), config.persona_name),
                "description": normalize_scalar_field(
                    payload.get("persona_description"),
                    config.persona_description,
                ),
                "derived_from_group": config.group_id,
                "goals": normalize_items(payload.get("goals"), config.goals),
                "pain_points": normalize_items(payload.get("pain_points"), config.pain_points),
                "context": normalize_items(payload.get("context"), config.context),
                "constraints": normalize_items(payload.get("constraints"), config.constraints),
                "evidence_reviews": evidence_reviews,
            }
        )

    write_json(args.groups_output, {"groups": groups_output})
    write_json(args.personas_output, {"personas": personas_output})
    merge_prompt_file(
        args.prompt_output,
        {
            "model": MODEL_NAME,
            "review_grouping_prompt_template": GROUPING_PROMPT_TEMPLATE,
            "persona_generation_prompt_template": GROUPING_PROMPT_TEMPLATE,
        },
    )

    print(f"Wrote automated review groups to {args.groups_output}")
    print(f"Wrote automated personas to {args.personas_output}")
    print(f"Updated prompt file at {args.prompt_output}")


if __name__ == "__main__":
    main()
