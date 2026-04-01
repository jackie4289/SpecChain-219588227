"""Collect Google Play reviews for one app and save them as JSONL."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google_play_scraper import Sort, app, reviews

DEFAULT_APP_ID = "meditofoundation.medito"
DEFAULT_TARGET_COUNT = 5000
DEFAULT_OUTPUT = Path("data/reviews_raw.jsonl")
DEFAULT_METADATA = Path("data/dataset_metadata.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect reviews from Google Play Store for one app."
    )
    parser.add_argument("--app-id", default=DEFAULT_APP_ID, help="Google Play app id")
    parser.add_argument(
        "--target-count",
        type=int,
        default=DEFAULT_TARGET_COUNT,
        help="Maximum number of reviews to collect",
    )
    parser.add_argument("--lang", default="en", help="Review language")
    parser.add_argument("--country", default="us", help="Store country")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to output raw JSONL file",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA,
        help="Path to metadata JSON file",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Reviews fetched per API call",
    )
    return parser.parse_args()


def to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()
    return str(value)


def get_app_details(app_id: str, lang: str, country: str) -> dict[str, Any]:
    return app(app_id, lang=lang, country=country)


def collect_reviews(
    app_id: str,
    target_count: int,
    lang: str,
    country: str,
    batch_size: int,
) -> list[dict[str, Any]]:
    continuation_token = None
    collected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    while len(collected) < target_count:
        this_batch = min(batch_size, target_count - len(collected))
        result, continuation_token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=this_batch,
            continuation_token=continuation_token,
            filter_score_with=None,
        )

        if not result:
            break

        for row in result:
            review_id = str(row.get("reviewId") or "").strip()
            if review_id and review_id in seen_ids:
                continue
            if review_id:
                seen_ids.add(review_id)

            collected.append(
                {
                    "app_id": app_id,
                    "review_id": review_id or None,
                    "user_name": row.get("userName"),
                    "score": row.get("score"),
                    "thumbs_up_count": row.get("thumbsUpCount"),
                    "review_created_version": row.get("reviewCreatedVersion"),
                    "at": to_iso(row.get("at")),
                    "reply_content": row.get("replyContent"),
                    "replied_at": to_iso(row.get("repliedAt")),
                    "content": row.get("content"),
                }
            )

            if len(collected) >= target_count:
                break

        if continuation_token is None:
            break

    return collected


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_metadata(
    app_details: dict[str, Any],
    args: argparse.Namespace,
    extracted_count: int,
) -> dict[str, Any]:
    available_reviews = app_details.get("reviews")
    if isinstance(available_reviews, int) and available_reviews >= extracted_count:
        limitation_note = (
            f"Google Play metadata reports {available_reviews} reviews; extracted "
            f"{extracted_count} reviews."
        )
    elif isinstance(available_reviews, int):
        limitation_note = (
            f"Google Play metadata reports {available_reviews} reviews, but the API "
            f"returned {extracted_count} review records. The metadata field likely "
            "represents a subset; extracted the full target count."
        )
    else:
        limitation_note = (
            f"Google Play total review count was unavailable; extracted {extracted_count} "
            "reviews."
        )

    return {
        "app_name": app_details.get("title"),
        "app_id": args.app_id,
        "dataset_size": {
            "raw_reviews": extracted_count,
            "clean_reviews": None,
        },
        "collection_method": {
            "source": "Google Play Store",
            "tool": "google-play-scraper",
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "parameters": {
                "lang": args.lang,
                "country": args.country,
                "sort": "NEWEST",
                "target_count": args.target_count,
                "batch_size": args.batch_size,
            },
            "google_play_stats": {
                "ratings": app_details.get("ratings"),
                "reviews": app_details.get("reviews"),
                "score": app_details.get("score"),
                "installs": app_details.get("installs"),
            },
            "limitation_note": limitation_note,
        },
        "cleaning_decisions": [],
    }


def write_metadata(metadata: dict[str, Any], metadata_path: Path) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()

    app_details = get_app_details(args.app_id, args.lang, args.country)
    records = collect_reviews(
        app_id=args.app_id,
        target_count=args.target_count,
        lang=args.lang,
        country=args.country,
        batch_size=args.batch_size,
    )

    write_jsonl(records, args.output)
    metadata = build_metadata(app_details, args, len(records))
    write_metadata(metadata, args.metadata)

    print(
        f"Collected {len(records)} reviews for {app_details.get('title')} "
        f"({args.app_id}) into {args.output}"
    )
    print(f"Metadata written to {args.metadata}")


if __name__ == "__main__":
    main()
