---
name: wiki-trends
description: >
  Analyze Wikipedia pageview trends across languages to evaluate topic interest
  for B2C product strategy. Fetches Wikimedia pageview metrics, resolves article
  titles across languages, analyzes growth and confidence with linear regression,
  generates comparison charts (PNG), and produces one-page executive PDF reports.
  Use when users ask about topic popularity, audience interest across Wikipedia
  language editions, market demand validation, or comparing topic trajectories.
compatibility: Requires Python 3.10+ and outbound internet access for Wikimedia API endpoints.
metadata:
  author: wiki-trends-team
  version: "1.0"
---

# Wikipedia Trends Skill

A specialized skill for extracting, comparing, and interpreting Wikipedia reading trends across languages and timeframes to inform product decisions.

## Quick Start (Happy Path)

To perform an end-to-end analysis comparing interest in a topic across languages over the last 2 years, run the single `pipeline` command:

```powershell
# PowerShell (Windows)
.\scripts\.venv\Scripts\python.exe scripts/wiki_trends.py pipeline `
  --topic "Intermittent fasting" `
  --langs pl,cs `
  --period 2y `
  --chart-output fasting_trends.png `
  --output fasting_report.pdf
```

```bash
# Linux / macOS / Bash
./scripts/.venv/bin/python scripts/wiki_trends.py pipeline \
  --topic "Intermittent fasting" \
  --langs pl,cs \
  --period 2y \
  --chart-output fasting_trends.png \
  --output fasting_report.pdf
```

The pipeline command executes the entire sequence:
1. Resolves topic names in target language wikis via MediaWiki langlinks.
2. Fetches monthly user pageviews via Wikimedia REST API.
3. Computes linear regression, growth percentage, R² fit, and confidence scores.
4. Generates a comparison line chart with trend lines (`.png`).
5. Generates a publication-grade one-page executive PDF report (`.pdf`).
6. Emits structured JSON on `stdout` while logging details to a `.log` file.

---

## Environment Setup

Before the first run, initialize the environment:

```bash
python scripts/setup.py
```
This script creates a virtual environment at `scripts/.venv` and installs all dependencies (`requests`, `matplotlib`, `numpy`, `scipy`, `reportlab`).

---

## Commands Reference

The CLI entry point is `scripts/wiki_trends.py`. Standard logs go to a `.log` file (default: `wiki_trends.log`); clean JSON is emitted on `stdout`.

| Subcommand | Purpose | Key Parameters |
|---|---|---|
| `pipeline` | Full end-to-end execution | `--topic`, `--langs`, `--period` (`6m`, `1y`, `2y`, `3y`), `--output` |
| `resolve` | Cross-language article title resolution | `--topic`, `--source-lang` (default `en`), `--target-langs` (comma-separated) |
| `fetch` | Fetch pageviews time series | `--articles` (JSON or file), `--start`, `--end`, `--granularity` (`monthly`/`daily`) |
| `analyze` | Run statistical trend analysis | `--input` (data JSON file or `-` for stdin) |
| `chart` | Generate PNG line chart | `--input` (data JSON), `--output`, `--title`, `--trend-lines` |
| `report` | Generate one-page PDF report | `--input` (data JSON), `--chart` (PNG), `--topic`, `--output` |

Global flags:
- `-v`, `--verbose`: Enable debug logging.
- `-q`, `--quiet`: Suppress informative logs (errors/warnings only).
- `--log-file`: Path to output log file (default: `wiki_trends.log`).


---

## Workflow: Answering User Queries

### Step 1: Clarify Query Parameters
- **Topic**: What concept is the user asking about? (e.g., "Astronomy", "Language learning").
- **Languages**: Which Wikipedia language editions are relevant? (e.g., `pl` for Polish, `cs` for Czech, `uk` for Ukrainian, `de` for German).
- **Timeframe**: Defaults to `2y` (2 years monthly) for strategic product decisions; use `1y` or `3y` if requested.

### Step 2: Run the Pipeline
Run `wiki_trends.py pipeline` with the extracted parameters. For piped workflows or iterative analysis, run subcommands individually (`resolve` -> `fetch` -> `analyze` -> `chart` -> `report`).

### Step 3: Interpret Metrics for the User
Examine the returned JSON structure:
- **`direction`**:
  - `growing`: Upward slope with statistical significance or >10% growth.
  - `declining`: Downward slope with statistical significance or <-10% decline.
  - `stable`: Flat or oscillating within bounds.
- **`confidence`**:
  - `high`: R² > 0.60 and p-value < 0.05. Strong, consistent trend.
  - `medium`: R² > 0.30 or p-value < 0.10. Moderate signal, some fluctuation.
  - `low`: R² ≤ 0.30 or p-value ≥ 0.10. High noise; do not treat as definitive.
- **`total_growth_pct`**: Smoothed percentage change comparing the start and end of the period.
- **`volatility`**: Ratio of standard deviation to mean (>0.5 indicates sharp peaks or seasonality).

### Step 4: Present Deliverables & Insights
Always present to the user:
1. **Direct Answer**: Clear verdict on growth, ranking, and confidence.
2. **Key Metrics Summary**: Monthly views, growth rate, and trend direction.
3. **Artifact Links**: Link to the generated `.png` chart and `.pdf` report.
4. **Mandatory Caveats**: Ground the conclusions in reality.

---

## Mandatory Caveats (Always State to Users)

Whenever presenting findings from Wikipedia pageview trends, explicitly state:
1. **Reading Interest ≠ Willingness to Pay**: High Wikipedia pageviews indicate educational curiosity or cultural awareness, not commercial intent or paying customer demand.
2. **Market Scale vs. Growth Rate**: Small language editions (e.g., Czech or Ukrainian) may display high percentage growth on low absolute view counts, whereas large editions (English, German) may display modest growth on millions of views.
3. **External Spikes & Academic Seasonality**: Sudden spikes are often triggered by media events, school semesters, or exam periods rather than permanent shifts in lifestyle habits.

---

## Handling Common Situations

- **Article Title Differs by Language**: Handled automatically by the `resolve` step using MediaWiki `langlinks`. If a direct title lookup fails, it automatically falls back to full-text search.
- **Article Not Found in Target Language**: If a target language lacks an article, note in your response that the topic does not have a dedicated article in that Wikipedia edition (a sign of very early or niche local interest).
- **Zero Views / HTTP 404**: Wikimedia returns 404 for articles with no traffic in a period. The skill handles this gracefully by returning empty series without crashing.
- **Follow-up Queries**: If the user asks about an additional topic (e.g., comparing "Ketogenic diet" to "Intermittent fasting"), keep previous chart/data and fetch the new topic, then compare momentum.

---

## References & Examples

- Detailed Wikimedia API specifications: [references/wikimedia_api.md](references/wikimedia_api.md)
- Complete worked examples with sample user prompts and responses: [examples/example_queries.md](examples/example_queries.md)
