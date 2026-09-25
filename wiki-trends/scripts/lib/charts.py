"""Chart generation module for Wikipedia pageview trends."""
import os
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from .logger import log


def create_comparison_chart(
    datasets: Dict[str, List[Dict[str, Any]]],
    output_path: str,
    title: str = "Wikipedia Pageview Trends",
    show_trend_lines: bool = True
) -> str:
    """
    Generate a multi-language comparison line chart and save as PNG.
    
    Args:
        datasets: Dict mapping label to list of {'date': 'YYYY-MM-DD', 'views': int}
        output_path: File path to save PNG image
        title: Chart title
        show_trend_lines: Whether to overlay dashed linear regression lines
        
    Returns:
        Absolute path to the saved PNG file.
    """
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output) or ".", exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fafafa")
    
    # Grid & styling
    ax.grid(True, linestyle="--", alpha=0.5, color="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#666666")
    ax.spines["bottom"].set_color("#666666")
    
    colors = plt.cm.tab10.colors
    all_dates = []
    
    for idx, (label, data_points) in enumerate(datasets.items()):
        if not data_points:
            continue
            
        color = colors[idx % len(colors)]
        dates = [d["date"] for d in data_points]
        views = [d["views"] for d in data_points]
        all_dates.extend(dates)
        
        x_indices = np.arange(len(dates))
        
        # Plot primary line & dots
        ax.plot(x_indices, views, label=label, color=color, linewidth=2.2, marker="o", markersize=4, alpha=0.9)
        
        # Overlay regression trend line if requested and sufficient points
        if show_trend_lines and len(views) >= 3:
            poly = np.polyfit(x_indices, views, 1)
            trend_fn = np.poly1d(poly)
            ax.plot(x_indices, trend_fn(x_indices), color=color, linestyle="--", linewidth=1.2, alpha=0.65)
            
    # Set X-axis labels
    if datasets:
        first_series = next(iter(datasets.values()))
        if first_series:
            dates = [d["date"] for d in first_series]
            x_indices = np.arange(len(dates))
            ax.set_xticks(x_indices)
            
            # Format labels (YYYY-MM) and thin out if too many
            if len(dates) > 18:
                step = max(1, len(dates) // 10)
                labels = [dates[i][:7] if i % step == 0 else "" for i in range(len(dates))]
            else:
                labels = [d[:7] for d in dates]
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9, color="#333333")
            
    # Y-axis thousands comma formatter
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    ax.tick_params(axis="both", which="major", labelsize=9, colors="#333333")
    
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14, color="#111111")
    ax.set_ylabel("Monthly Page Views", fontsize=10, fontweight="medium", labelpad=8, color="#333333")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e0e0e0", fontsize=9, loc="upper left")
    
    plt.tight_layout()
    plt.savefig(abs_output, bbox_inches="tight")
    plt.close(fig)
    
    size_kb = round(os.path.getsize(abs_output) / 1024, 1)
    log("CHART", f"Comparison chart saved: {abs_output} ({size_kb} KB, {len(datasets)} series)")
    return abs_output


def create_growth_bar_chart(growth_data: Dict[str, float], output_path: str, title: str = "Growth Comparison (%)") -> str:
    """
    Generate a bar chart comparing growth rates across languages/topics.
    
    Args:
        growth_data: Dict mapping label to growth percentage float
        output_path: Destination path
        title: Title of chart
    """
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output) or ".", exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fafafa")
    
    labels = list(growth_data.keys())
    values = [growth_data[l] for l in labels]
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in values]
    
    bars = ax.bar(labels, values, color=colors, width=0.5, alpha=0.85)
    ax.axhline(0, color="#666666", linewidth=0.8, linestyle="--")
    
    for bar in bars:
        height = bar.get_height()
        va = "bottom" if height >= 0 else "top"
        ax.annotate(f"{height:+.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3 if height >= 0 else -12),
                    textcoords="offset points",
                    ha="center", va=va, fontsize=9, fontweight="bold")
                    
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Growth Rate (%)", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(abs_output, bbox_inches="tight")
    plt.close(fig)
    
    log("CHART", f"Growth bar chart saved: {abs_output}")
    return abs_output
