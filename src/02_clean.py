"""Clean raw review dataset and export normalized JSONL."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
except ImportError:  # pragma: no cover - dependency availability varies by machine
    nltk = None
    stopwords = None
    WordNetLemmatizer = None

try:
    from num2words import num2words
except ImportError:  # pragma: no cover - dependency availability varies by machine
    num2words = None

DEFAULT_INPUT = Path("data/reviews_raw.jsonl")
DEFAULT_OUTPUT = Path("data/reviews_clean.jsonl")
DEFAULT_METADATA = Path("data/dataset_metadata.json")

WHITESPACE_RE = re.compile(r"\s+")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
NON_LETTER_RE = re.compile(r"[^a-zA-Z\s]")
FALLBACK_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "had",
    "has", "have", "he", "her", "him", "his", "i", "if", "in", "is", "it", "its",
    "me", "my", "of", "on", "or", "our", "she", "so", "that", "the", "their",
    "them", "there", "these", "they", "this", "to", "us", "was", "we", "were",
    "with", "you", "your",
}
SMALL_NUMBER_WORDS = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
}
TENS_WORDS = {
    20: "twenty",
    30: "thirty",
    40: "forty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean Google Play reviews dataset.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument(
        "--min-words",
        type=int,
        default=3,
        help="Minimum words after cleaning; shorter reviews are removed",
    )
    return parser.parse_args()


def ensure_nltk_resources() -> None:
    if nltk is None:
        return
    resources = [
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for lookup_path, resource_name in resources:
        try:
            nltk.data.find(lookup_path)
        except LookupError:
            nltk.download(resource_name, quiet=True)


def number_to_words(match: re.Match[str]) -> str:
    token = match.group(0).replace(",", "")
    if num2words is None:
        return fallback_number_to_words(token)
    try:
        if "." in token:
            converted = num2words(float(token))
        else:
            converted = num2words(int(token))
    except Exception:
        return fallback_number_to_words(token)
    return converted.replace("-", " ").replace(",", " ")


def extract_text(record: dict[str, Any]) -> str:
    for key in ("content", "review", "text", "review_text"):
        value = record.get(key)
        if isinstance(value, str):
            return value
    return ""


class IdentityLemmatizer:
    """Fallback rule-based lemmatizer used when NLTK is unavailable."""

    IRREGULARS = {
        "am": "be",
        "are": "be",
        "been": "be",
        "being": "be",
        "did": "do",
        "does": "do",
        "doing": "do",
        "had": "have",
        "has": "have",
        "having": "have",
        "is": "be",
        "ran": "run",
        "was": "be",
        "were": "be",
    }

    def lemmatize(self, token: str) -> str:
        return simple_lemma(token)


def fallback_number_to_words(token: str) -> str:
    if "." in token:
        left, right = token.split(".", 1)
        left_words = fallback_number_to_words(left) if left else "zero"
        right_words = " ".join(SMALL_NUMBER_WORDS.get(int(digit), digit) for digit in right if digit.isdigit())
        return f"{left_words} point {right_words}".strip()

    if not token.isdigit():
        return token

    number = int(token)
    if number < 20:
        return SMALL_NUMBER_WORDS[number]
    if number < 100:
        tens, ones = divmod(number, 10)
        tens_word = TENS_WORDS[tens * 10]
        return tens_word if ones == 0 else f"{tens_word} {SMALL_NUMBER_WORDS[ones]}"
    if number < 1000:
        hundreds, remainder = divmod(number, 100)
        head = f"{SMALL_NUMBER_WORDS[hundreds]} hundred"
        return head if remainder == 0 else f"{head} {fallback_number_to_words(str(remainder))}"
    if number < 1_000_000:
        thousands, remainder = divmod(number, 1000)
        head = f"{fallback_number_to_words(str(thousands))} thousand"
        return head if remainder == 0 else f"{head} {fallback_number_to_words(str(remainder))}"
    return " ".join(SMALL_NUMBER_WORDS.get(int(digit), digit) for digit in token)


def simple_lemma(token: str) -> str:
    irregular = IdentityLemmatizer.IRREGULARS.get(token)
    if irregular:
        return irregular

    if len(token) <= 3:
        return token

    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ves") and len(token) > 4:
        return token[:-3] + "f"
    if token.endswith(("ches", "shes", "xes", "zes", "ses")) and len(token) > 4:
        return token[:-2]
    if token.endswith("ing") and len(token) > 5:
        stem = token[:-3]
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        if stem.endswith(("at", "it", "iz", "ut", "iv")):
            return stem + "e"
        return stem
    if token.endswith("ied") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ed") and len(token) > 4:
        stem = token[:-2]
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        if stem.endswith(("at", "it", "iz", "ut", "v")):
            return stem + "e"
        return stem
    if token.endswith("s") and len(token) > 3 and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def build_language_tools() -> tuple[set[str], Any, list[str]]:
    notes: list[str] = []
    ensure_nltk_resources()

    if stopwords is not None and WordNetLemmatizer is not None:
        try:
            stop_words = set(stopwords.words("english"))
            lemmatizer = WordNetLemmatizer()
            return stop_words, lemmatizer, notes
        except LookupError:
            notes.append("NLTK resources were unavailable at runtime; used fallback stopwords, heuristic number conversion, and rule-based lemmatization.")

    notes.append("NLTK package was unavailable; used fallback stopwords, heuristic number conversion, and rule-based lemmatization.")
    return set(FALLBACK_STOPWORDS), IdentityLemmatizer(), notes


def clean_text(
    text: str,
    stop_words: set[str],
    lemmatizer: WordNetLemmatizer,
) -> str:
    text = text.strip().lower()
    text = NUMBER_RE.sub(number_to_words, text)
    text = NON_LETTER_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text).strip()
    if not text:
        return ""

    tokens = text.split(" ")
    tokens = [token for token in tokens if token and token not in stop_words]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    tokens = [token for token in tokens if token]
    return " ".join(tokens)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_metadata(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_metadata(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    stop_words, lemmatizer, fallback_notes = build_language_tools()

    raw_rows = load_jsonl(args.input)

    cleaned_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_clean_texts: set[str] = set()

    stats = {
        "input_rows": 0,
        "removed_empty": 0,
        "removed_duplicates": 0,
        "removed_too_short": 0,
        "output_rows": 0,
    }

    for row in raw_rows:
        stats["input_rows"] += 1

        review_id = str(row.get("review_id") or row.get("reviewId") or "").strip()
        if review_id:
            if review_id in seen_ids:
                stats["removed_duplicates"] += 1
                continue
            seen_ids.add(review_id)

        original_text = extract_text(row)
        if not original_text or not original_text.strip():
            stats["removed_empty"] += 1
            continue

        cleaned_text = clean_text(original_text, stop_words, lemmatizer)
        if not cleaned_text:
            stats["removed_empty"] += 1
            continue

        if len(cleaned_text.split()) < args.min_words:
            stats["removed_too_short"] += 1
            continue

        if cleaned_text in seen_clean_texts:
            stats["removed_duplicates"] += 1
            continue
        seen_clean_texts.add(cleaned_text)

        cleaned_rows.append(
            {
                "app_id": row.get("app_id"),
                "review_id": row.get("review_id") or row.get("reviewId"),
                "score": row.get("score"),
                "at": row.get("at"),
                "content_original": original_text.strip(),
                "content_clean": cleaned_text,
            }
        )

    stats["output_rows"] = len(cleaned_rows)
    write_jsonl(args.output, cleaned_rows)

    metadata = read_metadata(args.metadata)
    metadata.setdefault("dataset_size", {})
    metadata["dataset_size"]["raw_reviews"] = stats["input_rows"]
    metadata["dataset_size"]["clean_reviews"] = stats["output_rows"]
    metadata["cleaning_decisions"] = [
        "Removed duplicate reviews by review_id and duplicate cleaned text.",
        "Removed empty reviews and reviews with blank content.",
        f"Removed reviews with fewer than {args.min_words} words after cleaning.",
        "Lowercased all text.",
        "Converted numbers to text using num2words when available, otherwise a built-in fallback converter.",
        "Removed punctuation, special characters, and emojis using regex normalization.",
        "Collapsed extra whitespace.",
        "Removed English stop words using NLTK when available, otherwise a built-in fallback list.",
        "Lemmatized tokens with NLTK WordNetLemmatizer when available, otherwise used a built-in rule-based lemmatizer.",
    ]
    metadata["cleaning_decisions"].extend(fallback_notes)
    metadata["cleaning_stats"] = stats
    write_metadata(args.metadata, metadata)

    print(f"Read {stats['input_rows']} rows from {args.input}")
    print(f"Wrote {stats['output_rows']} cleaned rows to {args.output}")
    print(f"Updated metadata at {args.metadata}")


if __name__ == "__main__":
    main()
