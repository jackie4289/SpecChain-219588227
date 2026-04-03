"""Generate automated requirements from personas."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from automation_utils import (
    AMBIGUOUS_TERMS,
    MODEL_NAME,
    SPEC_PROMPT_TEMPLATE,
    extract_json_payload,
    fallback_requirements_for_group,
    format_requirement_block,
    get_groq_api_key,
    groq_chat,
    merge_prompt_file,
    read_json,
    require_groq_or_fallback,
    write_text,
)

DEFAULT_PERSONAS = Path("personas/personas_auto.json")
DEFAULT_OUTPUT = Path("spec/spec_auto.md")
DEFAULT_PROMPT_OUTPUT = Path("prompts/prompt_auto.json")

UNSUPPORTED_FRAGMENTS = (
    "users report",
    "rated ",
    "5-point",
    "survey",
    "personalized recommendation",
    "personalized recommendations",
    "function as expected",
    "work correctly",
    "accurately recorded",
    "clear and organized",
    "aid relaxation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate automated requirements from personas.")
    parser.add_argument("--personas", type=Path, default=DEFAULT_PERSONAS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prompt-output", type=Path, default=DEFAULT_PROMPT_OUTPUT)
    parser.add_argument("--api-key", default=None, help="Optional Groq API key override")
    return parser.parse_args()


def normalize_requirement_value(value: object) -> str:
    if isinstance(value, list):
        parts = [normalize_requirement_value(item) for item in value]
        return "; ".join(part for part in parts if part)
    if isinstance(value, dict):
        parts = [normalize_requirement_value(item) for item in value.values()]
        return "; ".join(part for part in parts if part)
    return str(value).strip()


def looks_valid_requirement(description: str, acceptance_criteria: str) -> bool:
    if not description or not acceptance_criteria:
        return False

    blob = f"{description} {acceptance_criteria}".lower()
    if any(fragment in blob for fragment in UNSUPPORTED_FRAGMENTS):
        return False
    if any(re.search(rf"\b{re.escape(term)}\b", blob) for term in AMBIGUOUS_TERMS):
        return False
    return True


def generate_requirements_for_persona(
    persona: dict[str, object],
    *,
    api_key: str | None,
) -> list[dict[str, str]]:
    require_groq_or_fallback(api_key, False)

    persona_summary = {
        "id": persona["id"],
        "name": persona["name"],
        "description": persona["description"],
        "derived_from_group": persona["derived_from_group"],
        "goals": persona.get("goals", []),
        "pain_points": persona.get("pain_points", []),
        "context": persona.get("context", []),
        "constraints": persona.get("constraints", []),
    }
    messages = [
        {"role": "system", "content": "You are a requirements analyst. Return JSON only."},
        {"role": "user", "content": SPEC_PROMPT_TEMPLATE.format(persona_summary=json.dumps(persona_summary, ensure_ascii=False))},
    ]
    response_text = groq_chat(messages, api_key=api_key)
    payload = extract_json_payload(response_text)
    if not isinstance(payload, dict) or not isinstance(payload.get("requirements"), list):
        raise ValueError("Expected a JSON object with a requirements list.")

    generated: list[dict[str, str]] = []
    for item in payload["requirements"][:2]:
        if not isinstance(item, dict):
            continue
        description = normalize_requirement_value(item.get("description"))
        acceptance_criteria = normalize_requirement_value(item.get("acceptance_criteria"))
        if looks_valid_requirement(description, acceptance_criteria):
            generated.append({"description": description, "acceptance_criteria": acceptance_criteria})

    fallback = fallback_requirements_for_group(str(persona["derived_from_group"]))
    if len(generated) < 2:
        generated.extend(fallback[len(generated) : 2])

    return generated[:2]


def main() -> None:
    args = parse_args()
    api_key = get_groq_api_key(args.api_key)
    require_groq_or_fallback(api_key, False)

    personas_payload = read_json(args.personas, {"personas": []})
    personas = personas_payload.get("personas", [])
    if not personas:
        raise RuntimeError(f"No personas found in {args.personas}")

    blocks: list[str] = ["# Automated Specification"]
    requirement_index = 1

    for persona in personas:
        requirements = generate_requirements_for_persona(
            persona,
            api_key=api_key,
        )
        source_persona = f"{persona['id']} - {persona['name']}"
        traceability = f"Derived from review group {persona['derived_from_group']}"
        for item in requirements:
            blocks.append(
                format_requirement_block(
                    requirement_id=f"FR_auto_{requirement_index}",
                    description=item["description"],
                    source_persona=source_persona,
                    traceability=traceability,
                    acceptance_criteria=item["acceptance_criteria"],
                )
            )
            requirement_index += 1

    write_text(args.output, "\n\n".join(blocks) + "\n")
    merge_prompt_file(
        args.prompt_output,
        {
            "model": MODEL_NAME,
            "spec_generation_prompt_template": SPEC_PROMPT_TEMPLATE,
        },
    )

    print(f"Wrote automated specification to {args.output}")


if __name__ == "__main__":
    main()
