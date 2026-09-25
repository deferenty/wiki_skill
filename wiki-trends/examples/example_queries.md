# Worked Examples: Wikipedia Trends Skill

This guide demonstrates how agents should interpret user questions, execute the CLI, analyze the JSON output, and format comprehensive responses with charts and reports.

---

## Example 1: Direct Cross-Language Comparison

### User Request
> "Compare growth of interest in intermittent fasting between Polish and Czech Wikipedia over the last two years."

### Agent Thought Process
1. **Topic**: "Intermittent fasting"
2. **Languages**: Polish (`pl`), Czech (`cs`)
3. **Period**: `2y` (two years monthly)
4. **Tool**: Execute the `pipeline` subcommand to resolve titles, pull data, compute trends, and generate charts.

### Command Executed
```bash
python scripts/wiki_trends.py pipeline \
  --topic "Intermittent fasting" \
  --langs pl,cs \
  --period 2y \
  --chart-output fasting_comparison.png \
  --output fasting_report.pdf
```

### Abbreviated JSON Output
```json
{
  "topic": "Intermittent fasting",
  "resolution": {
    "resolved": {
      "pl": "Post_przerywany",
      "cs": "Intermitentní_hladovění"
    }
  },
  "analysis": {
    "individual": {
      "pl": {
        "direction": "growing",
        "total_growth_pct": 34.2,
        "avg_views": 18450,
        "r_squared": 0.81,
        "p_value": 0.0002,
        "confidence": "high"
      },
      "cs": {
        "direction": "stable",
        "total_growth_pct": 8.4,
        "avg_views": 4120,
        "r_squared": 0.28,
        "p_value": 0.142,
        "confidence": "low"
      }
    },
    "correlations": {
      "pl-cs": 0.64
    },
    "ranking": ["pl", "cs"],
    "recommendation": "Strongest growth is in 'pl' (+34.2%, high confidence, ~18,450 avg views/mo)."
  },
  "chart_path": "c:/sources/wiki_skill/wiki-trends/fasting_comparison.png",
  "report_path": "c:/sources/wiki_skill/wiki-trends/fasting_report.pdf"
}
```

### Agent Response to User
> ### Intermittent Fasting: Polish vs. Czech Wikipedia Trend (2-Year Analysis)
>
> Over the past 24 months, **Polish Wikipedia demonstrates strong, statistically confident growth**, while **Czech Wikipedia remains relatively stable with lower baseline traffic**.
>
> #### Key Metrics
> | Language | Resolved Article | Monthly Average | 2-Year Growth | Trend & Confidence |
> |---|---|---|---|---|
> | **Polish (`pl`)** | *Post przerywany* | ~18,450 views | **+34.2%** | **Growing** (High confidence, R² = 0.81) |
> | **Czech (`cs`)** | *Intermitentní hladovění* | ~4,120 views | **+8.4%** | **Stable** (Low confidence, R² = 0.28) |
>
> #### Key Takeaways
> - **Higher Market Velocity in Poland**: The Polish edition exhibits consistent, linear monthly increases with low noise (p = 0.0002), indicating sustained public interest.
> - **Scale Disparity**: The Polish audience is roughly 4.5× larger in absolute monthly readership than the Czech audience.
>
> 📊 **Visual Chart**: [fasting_comparison.png](file:///c:/sources/wiki_skill/wiki-trends/fasting_comparison.png)  
> 📄 **Executive One-Page PDF Report**: [fasting_report.pdf](file:///c:/sources/wiki_skill/wiki-trends/fasting_report.pdf)
>
> *Note: Wikipedia readership reflects informational curiosity and health topic awareness, but does not guarantee commercial willingness to purchase a diet app or program.*

---

## Example 2: Single-Language Course Assessment with Confidence

### User Request
> "We're thinking of adding an astronomy course to an educational app. Is interest growing in Ukrainian Wikipedia, and how much can we trust that growth?"

### Agent Thought Process
1. **Topic**: "Astronomy" (source language `en`, target `uk`)
2. **Key Question**: Direction of growth AND statistical confidence / trust level.
3. **Execution**: Run `pipeline` for `uk` over a 3-year window to separate long-term trends from academic cycles.

### Command Executed
```bash
python scripts/wiki_trends.py pipeline \
  --topic "Astronomy" \
  --langs uk \
  --period 3y \
  --chart-output astronomy_uk.png \
  --output astronomy_report.pdf
```

### Abbreviated JSON Output
```json
{
  "topic": "Astronomy",
  "resolution": {
    "resolved": {
      "uk": "Астрономія"
    }
  },
  "analysis": {
    "individual": {
      "uk": {
        "direction": "stable",
        "total_growth_pct": 4.1,
        "avg_views": 14200,
        "r_squared": 0.12,
        "p_value": 0.28,
        "confidence": "low",
        "volatility": 0.42
      }
    },
    "anomalies": {
      "uk": [
        {"date": "2024-05-01", "views": 26800, "z_score": 2.34, "type": "spike"}
      ]
    }
  }
}
```

### Agent Response to User
> ### Astronomy on Ukrainian Wikipedia: Trend & Reliability Assessment
>
> **Direct Verdict:** Baseline interest in astronomy on Ukrainian Wikipedia is **stable rather than growing**, with **low statistical confidence** in any upward secular trend.
>
> #### Detailed Evaluation:
> - **Growth Rate**: +4.1% over 3 years (effectively flat).
> - **Confidence Score**: **Low** (R² = 0.12, p = 0.28). The variation in readership is predominantly driven by seasonal patterns rather than steady organic expansion.
> - **Seasonality & Spikes**: Notable spikes occur in April–May and September–October (up to 26,800 views/mo vs 14,200 baseline), correlating closely with the school/university academic calendar and exam periods.
>
> #### Product Implication:
> While there is healthy baseline volume (~14,000 readers/mo), demand is cyclical. An astronomy course should be positioned or marketed around academic calendar milestones rather than assuming a continuous wave of new organic interest.
>
> 📊 **Chart**: [astronomy_uk.png](file:///c:/sources/wiki_skill/wiki-trends/astronomy_uk.png)  
> 📄 **One-Page PDF Report**: [astronomy_report.pdf](file:///c:/sources/wiki_skill/wiki-trends/astronomy_report.pdf)

---

## Example 3: Multi-Language Market Research

### User Request
> "We're building a language learning app. Compare interest in 'learning English' across selected Wikipedia editions (Polish, Czech, Ukrainian, Romanian). Which audiences should we target first?"

### Command Executed
```bash
python scripts/wiki_trends.py pipeline \
  --topic "English language" \
  --langs pl,cs,uk,ro \
  --period 2y \
  --chart-output english_learning_compare.png \
  --output english_learning_report.pdf
```

### Agent Response to User
> ### Cross-Market Analysis: Interest in English Language Articles
>
> We analyzed reading trends across Polish, Czech, Ukrainian, and Romanian Wikipedia editions over the past 24 months.
>
> #### Audience Ranking & Trajectory
> 1. **Ukrainian (`uk`)**: Highest growth (+28.4%, Medium confidence, ~42,000 monthly views). Sustained upward trajectory, reflecting heightened regional demand for international communication and mobility.
> 2. **Polish (`pl`)**: Largest overall scale (~68,000 monthly views, +11.2% growth, Medium confidence). Large, mature, and consistent market.
> 3. **Romanian (`ro`)**: Moderate volume (~15,500 monthly views, +6.3% growth, Low confidence/stable).
> 4. **Czech (`cs`)**: Stable baseline (~12,800 monthly views, +2.1% growth, Low confidence).
>
> #### Recommended Prioritization
> - **Primary Target**: **Ukrainian** for top organic momentum; **Polish** for scale and stability.
> - **Secondary Target**: Romanian and Czech, where growth is currently static.
>
> 📊 **Comparison Chart**: [english_learning_compare.png](file:///c:/sources/wiki_skill/wiki-trends/english_learning_compare.png)  
> 📄 **Executive PDF Summary**: [english_learning_report.pdf](file:///c:/sources/wiki_skill/wiki-trends/english_learning_report.pdf)
>
> *Strategic Caution: High article views on 'English language' indicate broad educational interest. Pair this finding with local app store search volume (ASO) and competitors' pricing before committing localization budgets.*
