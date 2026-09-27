# Wikipedia Trends Agent Skill

A standardized [Agent Skills](https://agentskills.io/specification) compliant skill that empowers AI coding agents and LLMs to analyze Wikipedia reading interest across languages to inform B2C product decisions.

## Repository Overview

```
wiki_skill/
├── wiki-trends/                   # The Agent Skill package
│   ├── SKILL.md                   # Agent Skills spec entry point (<500 lines)
│   ├── scripts/
│   │   ├── requirements.txt       # Minimal Python dependencies
│   │   ├── setup.py               # One-step environment bootstrap
│   │   ├── wiki_trends.py         # Primary CLI entry point
│   │   └── lib/
│   │       ├── __init__.py
│   │       ├── api.py             # Wikimedia REST & MediaWiki client
│   │       ├── analysis.py        # Trend regression, confidence & correlation
│   │       ├── charts.py          # Clean publication PNG charts (matplotlib Agg)
│   │       ├── report.py          # One-page executive PDF report (reportlab)
│   │       └── logger.py          # Structured component logger to .log file
│   ├── references/
│   │   └── wikimedia_api.md       # Wikimedia API documentation & gotchas
│   └── examples/
│       └── example_queries.md     # Worked examples for AI agents
└── README.md                      # Project documentation
```

## Quick Start

### 1. Bootstrap Python Environment
```bash
cd wiki-trends/scripts
python setup.py
```
This automatically initializes a virtual environment in `wiki-trends/scripts/.venv` and installs required packages (`requests`, `matplotlib`, `numpy`, `scipy`, `reportlab`).

### 2. Run Single Pipeline Command
To analyze, chart, and generate a one-page PDF comparing topic momentum across languages:

**From `wiki-trends/` directory:**

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
# Bash (Linux / macOS / Git Bash)
./scripts/.venv/bin/python scripts/wiki_trends.py pipeline \
  --topic "Intermittent fasting" \
  --langs pl,cs \
  --period 2y \
  --chart-output fasting_trends.png \
  --output fasting_report.pdf
```

*(Alternatively, run as a single line without line continuations)*


## Architecture & Design Principles

- **Agent Skills Spec Compliance**: `wiki-trends/` contains a valid `SKILL.md` with required frontmatter (`name`, `description`, `compatibility`, `metadata`), kept under 500 lines for token economy on cheap models.
- **Pure JSON on stdout, Logs to .log file**: CLI subcommands emit clean JSON to stdout for piping and structured agent parsing, while rich diagnostic logs go to a `.log` file (default: `wiki_trends.log`).
- **Comprehensive API Logging**: Every outbound Wikimedia API call logs the exact URL, HTTP status code, response time in seconds, and item counts for full traceability.
- **Cross-Language Resolution**: Queries MediaWiki `action=query&prop=langlinks` to translate topics accurately across language wikis (e.g. "Intermittent fasting" -> Polish "Post przerywany", Czech "Intermitentní hladovění").
- **Statistical Rigor**: Calculates linear slope, goodness of fit ($R^2$), p-value, volatility, and categorical confidence levels (`high`, `medium`, `low`).
- **Strict One-Page PDF Reports**: Produces cleanly styled, self-contained executive PDFs including embedded trend charts, metrics tables, strategic takeaways, and methodological caveats.

## Development Roadmap

### Phase 2: Enhanced Analytics
- STL (Seasonal and Trend decomposition using LOESS) to isolate recurring academic seasonality.
- Rolling moving average smoothing options.
- Year-over-Year (YoY) comparison mode.

### Phase 3: Scalability & Performance
- Local file-based HTTP response caching to avoid redundant API queries.
- Asynchronous fetching for comparisons across 10+ languages.
- Direct CSV and Excel export options.

### Phase 4: Integrations
- Model Context Protocol (MCP) server wrapper for direct tool execution by Claude, Cursor, and ChatGPT.
- Automated alert triggers on sudden topic surges.
