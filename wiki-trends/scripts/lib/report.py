"""One-page PDF report generation module using ReportLab."""
from datetime import datetime
import os
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .logger import log

DEFAULT_LIMITATIONS = [
    "Wikipedia pageviews reflect educational/informational curiosity, not commercial purchase intent.",
    "Automated traffic is filtered using Wikimedia agent=user, but smaller language editions may exhibit higher baseline noise.",
    "Short analysis intervals can capture temporary news cycles or academic seasonality rather than secular product demand.",
]


def create_report(
    topic: str,
    period: str,
    chart_path: str,
    analysis_results: Dict[str, Any],
    output_path: str,
    insights: Optional[List[str]] = None,
    limitations: Optional[List[str]] = None,
) -> str:
    """
    Generate an executive one-page A4 PDF report with embedded chart, metrics table, and insights.
    
    Args:
        topic: Topic or query name
        period: Human-readable period string (e.g., "Jan 2024 – Sep 2026")
        chart_path: Path to the generated comparison chart PNG
        analysis_results: Output dictionary from compare_trends()
        output_path: Destination path for the PDF
        insights: Optional custom insights list
        limitations: Optional custom limitations list
        
    Returns:
        Absolute path to the generated PDF.
    """
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output) or ".", exist_ok=True)
    
    # A4: 595.27 x 841.89 points
    margin = 36  # 0.5 inch margins
    printable_width = 595.27 - (margin * 2)  # ~523 pt
    
    doc = SimpleDocTemplate(
        abs_output,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1a202c"),
        spaceAfter=2,
    )
    
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4a5568"),
    )
    
    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2b6cb0"),
        spaceBefore=6,
        spaceAfter=4,
    )
    
    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#2d3748"),
    )
    
    bullet_style = ParagraphStyle(
        "BulletText",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2,
    )
    
    caveat_style = ParagraphStyle(
        "CaveatText",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#718096"),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2,
    )
    
    elements = []
    
    # 1. Header
    elements.append(Paragraph(f"Wikipedia Trend Analysis: {topic}", title_style))
    today_str = datetime.now().strftime("%Y-%m-%d")
    meta_text = f"<b>Analyzed Period:</b> {period} &nbsp;|&nbsp; <b>Report Generated:</b> {today_str} &nbsp;|&nbsp; <b>Source:</b> Wikimedia API (agent=user)"
    elements.append(Paragraph(meta_text, subtitle_style))
    elements.append(Spacer(1, 8))
    
    # 2. Embedded Chart
    if os.path.exists(chart_path):
        # Fit nicely within ~523 pt width, 220 pt height
        chart_img = Image(chart_path, width=printable_width, height=215)
        elements.append(chart_img)
        elements.append(Spacer(1, 8))
        
    # 3. Key Metrics Table
    elements.append(Paragraph("Key Trend & Confidence Metrics", section_heading_style))
    
    table_data = [
        ["Language / Edition", "Monthly Avg", "Total Growth", "Trend Direction", "Confidence", "Fit (R²)"]
    ]
    
    individual = analysis_results.get("individual", {})
    for label, metrics in individual.items():
        growth = metrics.get("total_growth_pct", 0.0)
        growth_str = f"{growth:+.1f}%"
        direction = metrics.get("direction", "unknown").capitalize()
        confidence = metrics.get("confidence", "low").capitalize()
        avg_views = f"{int(metrics.get('avg_views', 0)):,}"
        r2 = f"{metrics.get('r_squared', 0.0):.2f}"
        
        table_data.append([
            label,
            avg_views,
            growth_str,
            direction,
            confidence,
            r2
        ])
        
    col_widths = [110, 75, 75, 95, 85, 80]
    metric_table = Table(table_data, colWidths=col_widths, hAlign="LEFT")
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
    ]))
    elements.append(metric_table)
    elements.append(Spacer(1, 8))
    
    # 4. Strategic Insights & Synthesis
    elements.append(Paragraph("Strategic Findings & Recommendations", section_heading_style))
    
    computed_insights = list(insights) if insights else []
    if not computed_insights:
        recommendation = analysis_results.get("recommendation")
        if recommendation:
            computed_insights.append(recommendation)
        ranking = analysis_results.get("ranking", [])
        if ranking:
            top = ranking[0]
            top_growth = individual.get(top, {}).get("total_growth_pct", 0)
            computed_insights.append(
                f"Market prioritization: '{top}' demonstrates the highest relative trajectory ({top_growth:+.1f}%)."
            )
        corrs = analysis_results.get("correlations", {})
        if corrs:
            high_corrs = [f"{k} (r={v})" for k, v in corrs.items() if v >= 0.7]
            if high_corrs:
                computed_insights.append(
                    f"Strong synchronization observed across audiences: {', '.join(high_corrs)}."
                )
                
    for ins in computed_insights[:3]:  # Keep to top 3 to guarantee 1 page
        elements.append(Paragraph(f"• {ins}", bullet_style))
        
    elements.append(Spacer(1, 8))
    
    # 5. Limitations & Caveats
    elements.append(Paragraph("Critical Methodological Limitations", section_heading_style))
    active_limitations = limitations or DEFAULT_LIMITATIONS
    for lim in active_limitations:
        elements.append(Paragraph(f"• {lim}", caveat_style))
        
    # Build document
    doc.build(elements)
    
    size_kb = round(os.path.getsize(abs_output) / 1024, 1)
    log("REPORT", f"One-page PDF report generated: {abs_output} ({size_kb} KB)")
    return abs_output
