#!/usr/bin/env python3
"""
Wikipedia Trends CLI — Analyze Wikipedia pageview trends across languages.
Agent Skills format CLI entry point.
"""
import argparse
from datetime import datetime, timedelta
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path so lib can be imported when running script directly
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from lib.logger import log, setup_logger
from lib.api import resolve_article, fetch_pageviews, fetch_multi
from lib.analysis import analyze_trend, compare_trends, detect_anomalies, detect_seasonality
from lib.charts import create_comparison_chart, create_growth_bar_chart
from lib.report import create_report


def parse_period_shorthand(period: str) -> tuple[str, str]:
    """
    Parse shorthand period (e.g., '6m', '1y', '2y', '3y', '5y') into start and end dates (YYYYMMDD).
    To avoid partial month distortion, the end date defaults to the last completed full month.
    """
    now = datetime.now()
    first_of_this_month = datetime(now.year, now.month, 1)
    last_completed = (first_of_this_month - timedelta(days=1)).replace(day=1)
    end_dt = last_completed
    
    period = period.strip().lower()
    if period.endswith("y"):
        years = int(period[:-1])
        start_year = end_dt.year - years
        start_dt = datetime(start_year, end_dt.month, 1)
    elif period.endswith("m"):
        months = int(period[:-1])
        total_months = end_dt.year * 12 + end_dt.month - months
        start_year = total_months // 12
        start_month = total_months % 12
        if start_month == 0:
            start_month = 12
            start_year -= 1
        start_dt = datetime(start_year, start_month, 1)
    else:
        raise ValueError(f"Unsupported period shorthand '{period}'. Use format like '6m', '1y', '2y', '3y', '5y'.")
        
    return start_dt.strftime("%Y%m01"), end_dt.strftime("%Y%m01")


def read_input_json(input_arg: str) -> Dict[str, Any]:
    """Read JSON from file path, stdin if '-', or parsed string."""
    if input_arg == "-":
        log("CMD", "Reading input JSON from stdin")
        return json.load(sys.stdin)
    if os.path.exists(input_arg):
        log("CMD", f"Reading input JSON from {input_arg}")
        with open(input_arg, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        return json.loads(input_arg)
    except json.JSONDecodeError:
        try:
            import ast
            val = ast.literal_eval(input_arg)
            if isinstance(val, dict):
                return val
        except Exception:
            pass
        if ":" in input_arg:
            pairs = [p.strip() for p in input_arg.strip("{}").split(",") if ":" in p]
            if pairs:
                d = {}
                for p in pairs:
                    k, v = p.split(":", 1)
                    d[k.strip().strip("'\"")] = v.strip().strip("'\"")
                return d
        raise FileNotFoundError(f"Input file not found or invalid JSON string: '{input_arg}'")


def cmd_resolve(args: argparse.Namespace) -> int:
    target_langs = [l.strip() for l in args.target_langs.split(",") if l.strip()]
    res = resolve_article(args.topic, source_lang=args.source_lang, target_langs=target_langs)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    articles_data = read_input_json(args.articles)
    if "resolved" in articles_data:
        articles = articles_data["resolved"]
    elif isinstance(articles_data, dict):
        articles = articles_data
    else:
        log("ERROR", "Articles parameter must be a JSON object mapping language to article title")
        return 1
        
    start_date = args.start
    end_date = args.end
    if args.period:
        start_date, end_date = parse_period_shorthand(args.period)
        
    if not start_date or not end_date:
        log("ERROR", "Either --period or both --start and --end must be specified")
        return 1
        
    res = fetch_multi(articles, start=start_date, end=end_date, granularity=args.granularity)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    data_input = read_input_json(args.input)
    datasets = data_input.get("data", data_input)
    res = compare_trends(datasets)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def cmd_chart(args: argparse.Namespace) -> int:
    data_input = read_input_json(args.input)
    datasets = data_input.get("data", data_input)
    chart_path = create_comparison_chart(
        datasets,
        output_path=args.output,
        title=args.title,
        show_trend_lines=args.trend_lines
    )
    size_kb = round(os.path.getsize(chart_path) / 1024, 1)
    res = {"chart_path": chart_path, "size_kb": size_kb}
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    data_input = read_input_json(args.input)
    datasets = data_input.get("data", data_input)
    
    if args.analysis:
        analysis_data = read_input_json(args.analysis)
    else:
        analysis_data = compare_trends(datasets)
        
    report_path = create_report(
        topic=args.topic,
        period=args.period or "Recent Period",
        chart_path=args.chart,
        analysis_results=analysis_data,
        output_path=args.output
    )
    size_kb = round(os.path.getsize(report_path) / 1024, 1)
    res = {"report_path": report_path, "size_kb": size_kb}
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    start_time = datetime.now()
    log("SETUP", f"Starting full pipeline for topic '{args.topic}'...")
    
    target_langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    
    # 1. Resolve
    log("RESOLVE", f"Resolving articles for languages: {target_langs}")
    res_obj = resolve_article(args.topic, source_lang=args.source_lang, target_langs=target_langs)
    resolved_articles = res_obj.get("resolved", {})
    
    if not resolved_articles:
        log("ERROR", f"No articles could be resolved for '{args.topic}' in specified languages")
        return 1
        
    # 2. Determine dates
    if args.period:
        start_date, end_date = parse_period_shorthand(args.period)
    else:
        start_date = args.start or "20240101"
        end_date = args.end or datetime.now().strftime("%Y%m01")
        
    # 3. Fetch
    log("FETCH", f"Fetching data from {start_date} to {end_date}...")
    fetch_obj = fetch_multi(resolved_articles, start=start_date, end=end_date, granularity=args.granularity)
    data = fetch_obj.get("data", {})
    
    # 4. Analyze
    log("ANALYSIS", "Running statistical trend analysis...")
    analysis_obj = compare_trends(data)
    
    # 5. Chart
    chart_output = args.chart_output or "chart.png"
    log("CHART", f"Generating comparison chart to {chart_output}...")
    chart_title = f"Wikipedia Pageview Trends: {args.topic}"
    chart_path = create_comparison_chart(data, output_path=chart_output, title=chart_title, show_trend_lines=True)
    
    # 6. Report
    report_output = args.output or "report.pdf"
    human_period = f"{start_date[:4]}-{start_date[4:6]} to {end_date[:4]}-{end_date[4:6]}"
    log("REPORT", f"Generating one-page executive PDF report to {report_output}...")
    report_path = create_report(
        topic=args.topic,
        period=human_period,
        chart_path=chart_path,
        analysis_results=analysis_obj,
        output_path=report_output
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    log("DONE", f"Pipeline completed in {elapsed:.2f}s")
    
    result = {
        "topic": args.topic,
        "period": human_period,
        "start_date": start_date,
        "end_date": end_date,
        "resolution": res_obj,
        "analysis": analysis_obj,
        "chart_path": chart_path,
        "report_path": report_path,
        "execution_time_sec": round(elapsed, 2)
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wikipedia Trends — Analyze Wikipedia pageview trends for market research."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress logs, output warnings/errors only")
    parser.add_argument("--log-file", default=None, help="Path to log file (default: wiki_trends.log)")
    
    subparsers = parser.add_subparsers(dest="subcommand", required=True, help="Subcommand to execute")
    
    # resolve
    p_resolve = subparsers.add_parser("resolve", help="Find article titles across languages")
    p_resolve.add_argument("--topic", required=True, help="Topic or search query")
    p_resolve.add_argument("--source-lang", default="en", help="Source Wikipedia language (default: en)")
    p_resolve.add_argument("--target-langs", required=True, help="Comma-separated target language codes (e.g. pl,cs,uk)")
    
    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Fetch pageview time series data")
    p_fetch.add_argument("--articles", required=True, help="JSON string or file path mapping lang code to article title")
    p_fetch.add_argument("--period", help="Period shorthand (e.g. 6m, 1y, 2y, 3y)")
    p_fetch.add_argument("--start", help="Start date (YYYYMMDD or YYYY-MM-DD)")
    p_fetch.add_argument("--end", help="End date (YYYYMMDD or YYYY-MM-DD)")
    p_fetch.add_argument("--granularity", default="monthly", choices=["monthly", "daily"], help="Data granularity")
    
    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Perform statistical trend analysis on fetched data")
    p_analyze.add_argument("--input", required=True, help="Path to fetch output JSON file or '-' for stdin")
    
    # chart
    p_chart = subparsers.add_parser("chart", help="Generate comparison line chart (PNG)")
    p_chart.add_argument("--input", required=True, help="Path to fetch output JSON file or '-' for stdin")
    p_chart.add_argument("--output", default="chart.png", help="Output PNG path (default: chart.png)")
    p_chart.add_argument("--title", default="Wikipedia Pageview Trends", help="Chart title")
    p_chart.add_argument("--trend-lines", action="store_true", help="Overlay dashed linear regression trend lines")
    
    # report
    p_report = subparsers.add_parser("report", help="Generate one-page PDF report")
    p_report.add_argument("--input", required=True, help="Path to fetch output JSON file or '-' for stdin")
    p_report.add_argument("--analysis", help="Optional path to analyze output JSON file")
    p_report.add_argument("--chart", required=True, help="Path to chart PNG file")
    p_report.add_argument("--topic", required=True, help="Topic name")
    p_report.add_argument("--period", help="Human-readable period string")
    p_report.add_argument("--output", default="report.pdf", help="Output PDF path (default: report.pdf)")
    
    # pipeline
    p_pipeline = subparsers.add_parser("pipeline", help="Run end-to-end: resolve -> fetch -> analyze -> chart -> report")
    p_pipeline.add_argument("--topic", required=True, help="Topic name or search term")
    p_pipeline.add_argument("--langs", required=True, help="Comma-separated language codes (e.g. pl,cs,uk)")
    p_pipeline.add_argument("--source-lang", default="en", help="Source Wikipedia language (default: en)")
    p_pipeline.add_argument("--period", default="2y", help="Period shorthand: 6m, 1y, 2y, 3y, 5y (default: 2y)")
    p_pipeline.add_argument("--start", help="Explicit start date (YYYYMMDD)")
    p_pipeline.add_argument("--end", help="Explicit end date (YYYYMMDD)")
    p_pipeline.add_argument("--granularity", default="monthly", choices=["monthly", "daily"], help="Granularity")
    p_pipeline.add_argument("--chart-output", default="chart.png", help="Path for chart PNG (default: chart.png)")
    p_pipeline.add_argument("--output", default="report.pdf", help="Path for PDF report (default: report.pdf)")
    
    parsed = parser.parse_args()
    setup_logger(verbose=parsed.verbose, quiet=parsed.quiet, log_file=parsed.log_file)
    
    try:
        if parsed.subcommand == "resolve":
            sys.exit(cmd_resolve(parsed))
        elif parsed.subcommand == "fetch":
            sys.exit(cmd_fetch(parsed))
        elif parsed.subcommand == "analyze":
            sys.exit(cmd_analyze(parsed))
        elif parsed.subcommand == "chart":
            sys.exit(cmd_chart(parsed))
        elif parsed.subcommand == "report":
            sys.exit(cmd_report(parsed))
        elif parsed.subcommand == "pipeline":
            sys.exit(cmd_pipeline(parsed))
    except Exception as e:
        log("ERROR", f"Command failed: {e}")
        if parsed.verbose:
            import traceback
            for line in traceback.format_exc().strip().splitlines():
                log("ERROR", line)
        sys.exit(1)


if __name__ == "__main__":
    main()
