# SpecChain Medito Project

Application studied: `Medito: Meditation & Sleep`

This repository implements the EECS 4312 SpecChain project for the Medito Android app. It contains a cleaned review dataset, manual/automated/hybrid requirements artifacts, validation tests, and comparison metrics across the three pipelines.

## Dataset

- Raw dataset: `data/reviews_raw.jsonl`
- Cleaned dataset: `data/reviews_clean.jsonl`
- Metadata: `data/dataset_metadata.json`
- Raw review count: `5000`
- Cleaned review count: `4006`

Data collection method:
- Source: Google Play Store
- App ID: `meditofoundation.medito`
- Tool: `google-play-scraper`
- Parameters: `lang=en`, `country=us`, `sort=NEWEST`, `target_count=5000`, `batch_size=200`
- Collection timestamp: `2026-04-01T16:53:01.282185+00:00`

Cleaning steps:
- Remove empty reviews
- Remove duplicate review IDs and duplicate cleaned text
- Remove reviews with fewer than 3 words after cleaning
- Lowercase text
- Convert numbers to text
- Remove punctuation, emojis, and special characters
- Collapse extra whitespace
- Remove stop words
- Lemmatize tokens

## Repository Structure

- `data/`: raw/clean datasets, metadata, and review groups
- `personas/`: manual, automated, and hybrid personas
- `spec/`: manual, automated, and hybrid specifications
- `tests/`: manual, automated, and hybrid validation tests
- `metrics/`: per-pipeline metrics and cross-pipeline summary
- `prompts/`: stored prompt templates used in the automated pipeline
- `reflection/`: final reflection
- `src/`: executable Python scripts for validation, cleaning, generation, and metrics

## Exact Commands

Validate the repository structure:

```powershell
python src/00_validate_repo.py
```

Rebuild the cleaned dataset and metadata:

```powershell
python src/02_clean.py
```

Set the Groq API key in the current PowerShell session before running the automated pipeline:

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

Run the full automated pipeline end to end:

```powershell
python src/run_all.py
```

Run the automated steps individually if needed:

```powershell
python src/05_personas_auto.py
python src/06_spec_generate.py
python src/07_tests_generate.py
python src/08_metrics.py --pipeline auto
```

Recompute metrics for the manual and hybrid artifacts:

```powershell
python src/08_metrics.py --pipeline manual
python src/08_metrics.py --pipeline hybrid
```

Open the comparison summary after running the metrics script:

```text
metrics/metrics_summary.json
```

## Current Metrics Snapshot

- Manual: `5` personas, `10` requirements, `20` tests
- Automated: `5` personas, `10` requirements, `20` tests
- Hybrid: `5` personas, `10` requirements, `20` tests

The detailed metric values are stored in `metrics/metrics_summary.json`.