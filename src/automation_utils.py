"""Shared helpers for the automated pipeline."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

GENERIC_THEME_STOPWORDS = {
    "app",
    "apps",
    "meditation",
    "meditations",
    "medito",
    "guided",
    "session",
    "sessions",
    "really",
    "great",
    "good",
    "best",
    "love",
    "amazing",
    "help",
    "helped",
    "using",
    "used",
    "use",
    "free",
    "thanks",
    "thank",
}

AMBIGUOUS_TERMS = (
    "easy",
    "easily",
    "better",
    "best",
    "simple",
    "quick",
    "quickly",
    "intuitive",
    "user-friendly",
    "seamless",
    "smooth",
    "relevant",
    "common",
    "minimal",
    "friendly",
)


@dataclass(frozen=True)
class ThemeConfig:
    key: str
    group_id: str
    default_theme: str
    persona_name: str
    persona_description: str
    keywords: tuple[str, ...]
    goals: tuple[str, ...]
    pain_points: tuple[str, ...]
    context: tuple[str, ...]
    constraints: tuple[str, ...]


THEME_CONFIGS: tuple[ThemeConfig, ...] = (
    ThemeConfig(
        key="pricing",
        group_id="A1",
        default_theme="Free access, optional donations, and ad-free value",
        persona_name="Free-First Value Seeker",
        persona_description=(
            "A user comparing meditation apps who cares most about real free access, "
            "optional donations, and an experience without ads or paywalls."
        ),
        keywords=(
            "free",
            "donate",
            "donation",
            "pay",
            "paid",
            "subscription",
            "subscriptions",
            "subscribe",
            "subscribtion",
            "subcription",
            "premium",
            "cost",
            "price",
            "ads",
            "ad",
            "ad-free",
            "no ads",
            "paywall",
        ),
        goals=(
            "Try the core content before deciding whether to donate",
            "Avoid subscriptions and third-party ads",
            "Use a meditation app that still feels polished without payment",
        ),
        pain_points=(
            "Donation prompts can feel close to a paywall",
            "Users question whether access is truly free",
            "Other apps interrupt meditation with ads or subscriptions",
        ),
        context=(
            "Comparing Medito with paid meditation apps",
            "Looking for low-cost wellness support",
            "Open to donating once the value is clear",
        ),
        constraints=(
            "Core content must remain available without payment",
            "Donation requests should stay optional and dismissible",
        ),
    ),
    ThemeConfig(
        key="sleep",
        group_id="A2",
        default_theme="Sleep support, sleep stories, and bedtime playback",
        persona_name="Nighttime Sleep Listener",
        persona_description=(
            "A user who opens Medito at bedtime and depends on sleep content, calm "
            "audio, and playback that stays out of the way."
        ),
        keywords=(
            "sleep",
            "sleeping",
            "asleep",
            "bed",
            "bedtime",
            "night",
            "insomnia",
            "story",
            "stories",
            "sleep story",
            "sleep stories",
            "sound",
            "sounds",
            "rain",
            "thunder",
            "nidra",
        ),
        goals=(
            "Fall asleep faster",
            "Keep calm audio playing through a bedtime routine",
            "Pick sleep content without extra effort",
        ),
        pain_points=(
            "Interrupted playback breaks the bedtime routine",
            "One track is not always enough to fall asleep",
            "Users want sleep content grouped together clearly",
        ),
        context=(
            "Using the app in bed, often with the screen dimmed or off",
            "Returning to the app when waking during the night",
            "Using sleep stories, sounds, and meditations interchangeably",
        ),
        constraints=(
            "Sleep playback should avoid blocking interruptions",
            "Bedtime content should be easy to reach in a low-effort flow",
        ),
    ),
    ThemeConfig(
        key="mental_health",
        group_id="A3",
        default_theme="Anxiety, stress, panic, and emotional support",
        persona_name="Stress Support Seeker",
        persona_description=(
            "A user who turns to Medito during anxiety, stress, grief, panic, or "
            "emotional overload and needs targeted support quickly."
        ),
        keywords=(
            "anxiety",
            "stress",
            "panic",
            "grief",
            "anger",
            "depression",
            "depressed",
            "mental",
            "mental health",
            "fear",
            "calm",
            "peace",
            "relax",
            "crisis",
            "emotion",
            "emotions",
            "grounding",
        ),
        goals=(
            "Find sessions that match the current emotional need",
            "Calm down during difficult moments",
            "Build more steady focus and peace over time",
        ),
        pain_points=(
            "The right session can be hard to find when someone is already stressed",
            "Some voices or formats work better than others during emotional strain",
            "Users need dependable support that feels easy to reach in the moment",
        ),
        context=(
            "Using the app during school, work, grief, or panic episodes",
            "Sometimes trying guided meditation for emotional regulation for the first time",
            "Wanting support that feels specific to the current need",
        ),
        constraints=(
            "Need-based content should be grouped clearly",
            "Helpful sessions should be easy to reopen later",
        ),
    ),
    ThemeConfig(
        key="habit_learning",
        group_id="A4",
        default_theme="Beginner guidance, courses, streaks, and daily practice",
        persona_name="Consistency-Building Beginner",
        persona_description=(
            "A new or returning meditator who relies on courses, reminders, and "
            "visible progress to build a steady meditation habit."
        ),
        keywords=(
            "beginner",
            "beginners",
            "course",
            "courses",
            "daily",
            "streak",
            "habit",
            "practice",
            "lesson",
            "lessons",
            "challenge",
            "challenges",
            "reminder",
            "track",
            "tracking",
            "journey",
        ),
        goals=(
            "Learn meditation step by step",
            "Keep a daily practice going",
            "See clear signs of progress over time",
        ),
        pain_points=(
            "Beginners do not always know where to start",
            "Consistency is harder without reminders or visible progress",
            "People want the app to surface the next step clearly when they return",
        ),
        context=(
            "Starting meditation for the first time or after a long gap",
            "Using beginner courses and short daily sessions",
            "Depending on reminders, streaks, or challenges to stay consistent",
        ),
        constraints=(
            "The next recommended lesson should be obvious",
            "Habit-building tools should be simple to turn on and keep using",
        ),
    ),
    ThemeConfig(
        key="reliability",
        group_id="A5",
        default_theme="Playback stability, updates, and progress continuity",
        persona_name="Reliability-Focused Daily User",
        persona_description=(
            "A frequent user who expects playback, search, login, and progress to "
            "keep working across updates, devices, and everyday interruptions."
        ),
        keywords=(
            "crash",
            "crashes",
            "crashing",
            "freeze",
            "frozen",
            "bug",
            "bugs",
            "issue",
            "issues",
            "audio",
            "playback",
            "player",
            "stop",
            "stopping",
            "stopped",
            "login",
            "sign",
            "search",
            "device",
            "devices",
            "sync",
            "synced",
            "progress",
            "queue",
            "repeat",
            "download",
            "offline",
            "network",
            "update",
            "timer",
            "working",
        ),
        goals=(
            "Finish sessions without crashes or audio cutouts",
            "Keep progress and streaks safe across devices",
            "Trust the app during daily use after updates",
        ),
        pain_points=(
            "Playback can crash, pause, or stop unexpectedly",
            "Updates can break search, login, or tracking behavior",
            "Progress can disappear after device changes or sign-in issues",
        ),
        context=(
            "Using the app daily and noticing regressions quickly",
            "Listening with headphones, screen off, or after an update",
            "Signing in across devices and expecting continuity",
        ),
        constraints=(
            "Core playback should stay stable during common interruptions",
            "Progress should sync back after sign-in on another device",
        ),
    ),
)

GROUPING_PROMPT_TEMPLATE = (
    "You are analyzing one automatically generated cluster of Medito app reviews. "
    "Return JSON only with keys theme, persona_name, persona_description, goals, "
    "pain_points, context, constraints. Keep every field grounded in the cluster "
    "summary. Do not invent age, job, or demographics. Use 2-4 concise items per "
    "list. Cluster summary: {cluster_summary}"
)

SPEC_PROMPT_TEMPLATE = (
    "You are writing software requirements for Medito from one persona. Return JSON "
    "only in this shape: {{\"requirements\": [{{\"description\": \"...\", "
    "\"acceptance_criteria\": \"...\"}}, {{\"description\": \"...\", "
    "\"acceptance_criteria\": \"...\"}}]}}. Write exactly 2 requirements. Ground every "
    "requirement in the persona summary only. Do not invent analytics, surveys, "
    "ratings, personalized recommendations, web support, or any feature that is not "
    "clearly implied by the persona. Keep each description to one sentence describing "
    "observable system behavior. Write each acceptance_criteria as one measurable "
    "sentence a tester can verify directly. Avoid vague terms like easy, better, "
    "intuitive, seamless, user-friendly, helpful, relevant, calm, or fast unless they "
    "are made measurable. Persona summary: {persona_summary}"
)

TEST_PROMPT_TEMPLATE = (
    "You are writing validation tests for one software requirement. Return JSON only "
    "with a key tests whose value is a list of exactly 2 objects. Each object must "
    "have scenario, steps, and expected_result. Steps should be short and concrete. "
    "Requirement summary: {requirement_summary}"
)


def load_reviews(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path, default: Any) -> Any:
    if not path.exists() or path.stat().st_size == 0:
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def merge_prompt_file(path: Path, updates: dict[str, Any]) -> None:
    current = read_json(path, {})
    if not isinstance(current, dict):
        current = {}
    current.update(updates)
    if current.get("prompt", "") == "" and any(key.endswith("_template") for key in current):
        current.pop("prompt", None)
    write_json(path, current)


def get_groq_api_key(explicit_key: str | None = None) -> str | None:
    return explicit_key or os.environ.get("GROQ_API_KEY")


def require_groq_or_fallback(api_key: str | None, allow_local_fallback: bool) -> None:
    if api_key or allow_local_fallback:
        return
    raise RuntimeError(
        "GROQ_API_KEY is not set. Set it in the environment or rerun with "
        "--allow-local-fallback for a local deterministic fallback."
    )


def groq_chat(
    messages: list[dict[str, str]],
    api_key: str,
    *,
    model: str = MODEL_NAME,
    temperature: float = 0.2,
    max_completion_tokens: int = 1400,
    retries: int = 3,
    timeout: int = 120,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
        "top_p": 1,
        "stream": False,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SpecChainTask4/1.0",
    }

    for attempt in range(1, retries + 1):
        request = urllib.request.Request(GROQ_CHAT_URL, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            if exc.code in {429, 498, 500, 502, 503, 504} and attempt < retries:
                time.sleep(1.5 * attempt)
                continue
            raise RuntimeError(f"Groq API request failed with HTTP {exc.code}: {details}") from exc
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(1.5 * attempt)
                continue
            raise RuntimeError(f"Groq API request failed: {exc}") from exc

    raise RuntimeError("Groq API request failed after retries.")


def extract_json_payload(text: str) -> Any:
    candidates: list[str] = []
    stripped = text.strip()
    if stripped:
        candidates.append(stripped)

    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    candidates.extend(match.strip() for match in fenced if match.strip())

    first_obj = stripped.find("{")
    last_obj = stripped.rfind("}")
    if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
        candidates.append(stripped[first_obj : last_obj + 1])

    first_arr = stripped.find("[")
    last_arr = stripped.rfind("]")
    if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
        candidates.append(stripped[first_arr : last_arr + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Could not extract JSON from model output: {text[:300]}")


def normalize_items(value: Any, default_items: tuple[str, ...], *, max_items: int = 4) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        items = []
    if not items:
        items = list(default_items)
    return items[:max_items]


def keyword_patterns(config: ThemeConfig) -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []
    for keyword in config.keywords:
        patterns.append(re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE))
    return patterns


def assign_reviews_to_themes(reviews: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    texts = [review["content_clean"] for review in reviews]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=3, max_df=0.7)
    matrix = vectorizer.fit_transform(texts)
    theme_patterns = {config.key: keyword_patterns(config) for config in THEME_CONFIGS}

    seed_scores: list[dict[str, int]] = []
    seeded_assignments: dict[int, str] = {}

    for index, review in enumerate(reviews):
        source = f"{review['content_clean']} {review['content_original']}"
        theme_score_map: dict[str, int] = {}
        for config in THEME_CONFIGS:
            score = sum(len(pattern.findall(source)) for pattern in theme_patterns[config.key])
            theme_score_map[config.key] = score
        seed_scores.append(theme_score_map)
        best_theme = max(theme_score_map, key=theme_score_map.get)
        if theme_score_map[best_theme] > 0:
            seeded_assignments[index] = best_theme

    centroids: dict[str, np.ndarray] = {}
    for config in THEME_CONFIGS:
        theme_indexes = [index for index, theme_key in seeded_assignments.items() if theme_key == config.key]
        if not theme_indexes:
            theme_indexes = list(range(min(10, len(reviews))))
        centroids[config.key] = np.asarray(matrix[theme_indexes].mean(axis=0))

    grouped_indexes: dict[str, list[int]] = {config.key: [] for config in THEME_CONFIGS}
    review_similarities: dict[tuple[str, int], float] = {}

    for index in range(len(reviews)):
        if index in seeded_assignments:
            theme_key = seeded_assignments[index]
            similarity = float(cosine_similarity(matrix[index], centroids[theme_key])[0, 0])
            grouped_indexes[theme_key].append(index)
            review_similarities[(theme_key, index)] = similarity
            continue

        similarities = {
            config.key: float(cosine_similarity(matrix[index], centroids[config.key])[0, 0])
            for config in THEME_CONFIGS
        }
        best_theme = max(similarities, key=similarities.get)
        grouped_indexes[best_theme].append(index)
        review_similarities[(best_theme, index)] = similarities[best_theme]

    feature_names = np.array(vectorizer.get_feature_names_out())
    cluster_data: dict[str, dict[str, Any]] = {}

    for config in THEME_CONFIGS:
        indexes = grouped_indexes[config.key]
        centroid = np.asarray(matrix[indexes].mean(axis=0)).ravel()
        ordered_terms = []
        for term in feature_names[np.argsort(centroid)[::-1]]:
            parts = term.split()
            if any(part in GENERIC_THEME_STOPWORDS for part in parts):
                continue
            ordered_terms.append(term)
            if len(ordered_terms) == 12:
                break

        ranked_indexes = sorted(
            indexes,
            key=lambda idx: (
                seed_scores[idx].get(config.key, 0),
                review_similarities.get((config.key, idx), 0.0),
                len(reviews[idx]["content_clean"]),
            ),
            reverse=True,
        )

        cluster_data[config.key] = {
            "config": config,
            "review_indexes": ranked_indexes,
            "top_keywords": ordered_terms,
            "cluster_size": len(indexes),
        }

    return cluster_data


def build_cluster_summary(cluster: dict[str, Any], reviews: list[dict[str, Any]], *, sample_size: int = 8) -> dict[str, Any]:
    review_indexes = cluster["review_indexes"]
    example_reviews = [reviews[index]["content_original"] for index in review_indexes[:sample_size]]
    return {
        "group_id": cluster["config"].group_id,
        "seed_theme": cluster["config"].default_theme,
        "cluster_size": cluster["cluster_size"],
        "top_keywords": cluster["top_keywords"],
        "sample_reviews": example_reviews,
    }


def parse_requirements(spec_text: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"## Requirement ID: (?P<id>[^\n]+)\n"
        r"- Description: \[(?P<description>.*?)\]\n"
        r"- Source Persona: \[(?P<source_persona>.*?)\]\n"
        r"- Traceability: \[(?P<traceability>.*?)\]\n"
        r"- Acceptance Criteria: \[(?P<acceptance_criteria>.*?)\]",
        flags=re.DOTALL,
    )
    requirements: list[dict[str, str]] = []
    for match in pattern.finditer(spec_text):
        requirements.append({key: value.strip() for key, value in match.groupdict().items()})
    return requirements


def format_requirement_block(requirement_id: str, description: str, source_persona: str, traceability: str, acceptance_criteria: str) -> str:
    return (
        f"## Requirement ID: {requirement_id}\n"
        f"- Description: [{description}]\n"
        f"- Source Persona: [{source_persona}]\n"
        f"- Traceability: [{traceability}]\n"
        f"- Acceptance Criteria: [{acceptance_criteria}]"
    )


def compute_traceability_links(
    review_groups: dict[str, Any],
    personas: dict[str, Any],
    requirements: list[dict[str, str]],
    tests: dict[str, Any],
) -> int:
    review_links = sum(len(group.get("review_ids", [])) for group in review_groups.get("groups", []))
    persona_group_links = sum(1 for persona in personas.get("personas", []) if persona.get("derived_from_group"))
    persona_evidence_links = sum(len(persona.get("evidence_reviews", [])) for persona in personas.get("personas", []))
    requirement_persona_links = sum(1 for requirement in requirements if requirement.get("source_persona"))
    requirement_group_links = sum(1 for requirement in requirements if requirement.get("traceability"))
    test_requirement_links = sum(1 for test in tests.get("tests", []) if test.get("requirement_id"))
    return (
        review_links
        + persona_group_links
        + persona_evidence_links
        + requirement_persona_links
        + requirement_group_links
        + test_requirement_links
    )


def compute_ambiguity_ratio(requirements: list[dict[str, str]]) -> float:
    if not requirements:
        return 0.0

    ambiguous = 0
    for requirement in requirements:
        blob = f"{requirement.get('description', '')} {requirement.get('acceptance_criteria', '')}".lower()
        if any(re.search(rf"\b{re.escape(term)}\b", blob) for term in AMBIGUOUS_TERMS):
            ambiguous += 1
    return round(ambiguous / len(requirements), 4)


def fallback_persona_payload(cluster: dict[str, Any]) -> dict[str, Any]:
    config: ThemeConfig = cluster["config"]
    return {
        "theme": config.default_theme,
        "persona_name": config.persona_name,
        "persona_description": config.persona_description,
        "goals": list(config.goals),
        "pain_points": list(config.pain_points),
        "context": list(config.context),
        "constraints": list(config.constraints),
    }


def fallback_requirements_for_group(group_id: str) -> list[dict[str, str]]:
    templates: dict[str, list[dict[str, str]]] = {
        "A1": [
            {
                "description": "Donation prompts should stay optional, and closing one should not block someone from starting a meditation session.",
                "acceptance_criteria": "Given someone closes a donation prompt while browsing or before playback, when the prompt disappears, then the selected session is still available to start without payment or account creation.",
            },
            {
                "description": "Core meditation content should stay free of third-party ads during browsing and playback.",
                "acceptance_criteria": "Given someone browses the home, course, and player screens for 15 minutes and finishes one session, when that flow ends, then no display, video, or audio ad has appeared.",
            },
        ],
        "A2": [
            {
                "description": "The app should offer a dedicated Sleep area with separate sections for sleep meditations, sleep stories, and sleep sounds.",
                "acceptance_criteria": "Given someone opens the Sleep area, when it loads, then sleep meditations, sleep stories, and sleep sounds appear as separate sections.",
            },
            {
                "description": "Sleep audio should support repeat and queued playback without interrupting the listener between tracks.",
                "acceptance_criteria": "Given someone queues two sleep tracks or turns on repeat for one track, when the first track ends, then the next track starts or the same track restarts automatically without a blocking popup.",
            },
        ],
        "A3": [
            {
                "description": "The app should let people browse sessions by named support categories such as Anxiety, Stress, Panic, Grief, and Anger.",
                "acceptance_criteria": "Given someone opens the needs-based browse area, when it loads, then Anxiety, Stress, Panic, Grief, and Anger appear as separate categories.",
            },
            {
                "description": "The app should let people reopen helpful support sessions from a saved favorites list in no more than two taps from the home screen.",
                "acceptance_criteria": "Given someone has saved at least one session as a favorite, when they open the home screen, then a favorite session can be started in no more than two taps.",
            },
        ],
        "A4": [
            {
                "description": "The beginner learning path should show lessons in order and surface the next unfinished lesson when someone returns.",
                "acceptance_criteria": "Given someone completes lesson 1 in the beginner course, when they reopen that course, then lesson 1 is marked complete and lesson 2 is shown as the next lesson.",
            },
            {
                "description": "The app should let people turn on one daily meditation reminder at a chosen local time.",
                "acceptance_criteria": "Given someone enables a daily reminder for 21:00 local time, when the reminder is saved, then that time is stored and one daily notification is scheduled for 21:00 until the reminder is turned off.",
            },
        ],
        "A5": [
            {
                "description": "A session should keep playing for at least 10 minutes with the screen off and headphones connected, without crashing or stopping before the 10-minute mark.",
                "acceptance_criteria": "Given someone starts a session, turns the screen off, and keeps wired or Bluetooth headphones connected, when 10 minutes pass, then audio is still playing, the app has not crashed, and playback controls respond after reopening the app.",
            },
            {
                "description": "A signed-in user's streak and course progress should be restored after sign-in and should carry across devices.",
                "acceptance_criteria": "Given someone completes a lesson on device A while signed in, when that same account is opened on device B or signs in again on the original device, then the updated streak count and completed lesson appear within 60 seconds after sync finishes.",
            },
        ],
    }
    return templates[group_id]


def fallback_tests_for_requirement(requirement: dict[str, str]) -> list[dict[str, Any]]:
    description = requirement["description"].lower()

    if "donation prompt" in description:
        return [
            {
                "scenario": "Close a donation prompt and continue into playback",
                "steps": ["Open a session that brings up a donation prompt", "Close the prompt", "Start the same session"],
                "expected_result": "The prompt closes and the selected session still starts without payment or account creation.",
            },
            {
                "scenario": "Dismiss a donation prompt while browsing",
                "steps": ["Open the home screen", "Bring up a donation prompt from a browse surface", "Close the prompt"],
                "expected_result": "The app stays on the same browsing flow and playback is still available.",
            },
        ]
    if "third-party ads" in description or "free of third-party ads" in description:
        return [
            {
                "scenario": "Browse the app without seeing ads",
                "steps": ["Open the home screen", "Spend 15 minutes moving between the home screen, course list, and one course page", "Watch the interface while browsing"],
                "expected_result": "No display, video, or audio ad appears while browsing.",
            },
            {
                "scenario": "Finish a session without ad interruptions",
                "steps": ["Start a guided meditation session", "Let the session play all the way through", "Watch the player during playback and after the session ends"],
                "expected_result": "No third-party ad appears before, during, or after the session.",
            },
        ]
    if "sleep area" in description:
        return [
            {
                "scenario": "Open the Sleep area",
                "steps": ["Open the home screen", "Go to the Sleep area", "Look at the sections shown there"],
                "expected_result": "Sleep meditations, sleep stories, and sleep sounds appear as separate sections.",
            },
            {
                "scenario": "Open each sleep section",
                "steps": ["Open the Sleep area", "Open sleep meditations, then go back", "Open sleep stories and sleep sounds"],
                "expected_result": "Each section opens its own list of sleep-related content.",
            },
        ]
    if "sleep audio should support repeat" in description or "queued playback" in description:
        return [
            {
                "scenario": "Play one sleep track into the next",
                "steps": ["Open any two sleep tracks", "Add both tracks to a queue", "Start the first track and let it finish"],
                "expected_result": "The second track starts automatically without a blocking popup.",
            },
            {
                "scenario": "Repeat one sleep track without interruption",
                "steps": ["Open a sleep track", "Turn on repeat", "Let the track reach the end"],
                "expected_result": "The same track starts again automatically without a blocking popup.",
            },
        ]
    if "browse sessions by named support categories" in description:
        return [
            {
                "scenario": "Open the support categories area",
                "steps": ["Open the browse area", "Go to the section organized by needs or support categories", "Inspect the category labels shown there"],
                "expected_result": "Anxiety, Stress, Panic, Grief, and Anger appear as separate categories.",
            },
            {
                "scenario": "Open one support category",
                "steps": ["Open the support categories area", "Select the Anxiety category", "Review the page that opens"],
                "expected_result": "A list of sessions for anxiety support is displayed.",
            },
        ]
    if "favorite" in description:
        return [
            {
                "scenario": "Save a support session as a favorite",
                "steps": ["Open a session detail page or player screen", "Use the favorite control to save the session", "Return to the home screen"],
                "expected_result": "The session is saved as a favorite and is available from the home screen.",
            },
            {
                "scenario": "Start a favorite from home",
                "steps": ["Make sure at least one session has been saved as a favorite", "Open the home screen", "Start the saved favorite from the visible home controls"],
                "expected_result": "The favorite session starts in no more than two taps.",
            },
        ]
    if "beginner learning path" in description or "beginner course" in description:
        return [
            {
                "scenario": "Show beginner lessons in order",
                "steps": ["Open the beginner course", "Look through the first several lessons", "Check whether the lesson order is fixed"],
                "expected_result": "The beginner course shows its lessons in a fixed order.",
            },
            {
                "scenario": "Return to the next beginner lesson",
                "steps": ["Finish lesson 1 in the beginner course", "Leave the course screen", "Open the beginner course again"],
                "expected_result": "Lesson 1 is marked complete and lesson 2 is shown as the next lesson.",
            },
        ]
    if "reminder" in description and "daily" in description:
        return [
            {
                "scenario": "Set a daily reminder",
                "steps": ["Open the reminder settings", "Set the reminder time to 21:00 local time", "Turn the reminder on and save it"],
                "expected_result": "The selected time is saved and one daily reminder is scheduled.",
            },
            {
                "scenario": "Turn a daily reminder off",
                "steps": ["Open reminder settings while a reminder is already enabled", "Turn the reminder off", "Save or exit settings"],
                "expected_result": "The reminder is shown as disabled and no active daily reminder remains scheduled.",
            },
        ]
    if "10 minutes" in description and "screen off" in description:
        return [
            {
                "scenario": "Keep playback going with the screen off",
                "steps": ["Start any guided session", "Connect wired or Bluetooth headphones", "Turn the screen off and wait 10 minutes"],
                "expected_result": "The audio keeps playing for the full 10-minute window without the app crashing.",
            },
            {
                "scenario": "Come back after screen-off playback",
                "steps": ["Start any guided session", "Turn the screen off while keeping the headphones connected", "Reopen the app after 10 minutes"],
                "expected_result": "The session is still active, the app has not crashed, and the playback controls still respond.",
            },
        ]
    if "streak" in description or "carry across devices" in description:
        return [
            {
                "scenario": "See progress carry over to another device",
                "steps": ["Sign in with the same account on device A and device B", "Complete one course lesson on device A", "Open the same course on device B and wait for sync"],
                "expected_result": "Within 60 seconds, device B shows the completed lesson and the updated streak count.",
            },
            {
                "scenario": "Get progress back after signing in again",
                "steps": ["Sign in to an account that already has progress", "Sign out and then sign back in with the same account", "Open the progress or course screen and wait for sync"],
                "expected_result": "Within 60 seconds, the earlier streak count and completed lessons are restored.",
            },
        ]
    return [
        {
            "scenario": f"Validate {requirement['id']} on the main user flow",
            "steps": ["Open the relevant area of the app", "Perform the action described by the requirement", "Observe the result"],
            "expected_result": "The result matches the requirement exactly.",
        },
        {
            "scenario": f"Validate {requirement['id']} after reopening the app",
            "steps": ["Complete the main requirement flow once", "Leave and reopen the app", "Return to the same feature"],
            "expected_result": "The requirement outcome remains visible and consistent after reopening the app.",
        },
    ]
