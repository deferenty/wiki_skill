"""Statistical analysis module for Wikipedia pageview time series."""
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import stats

from .logger import log


def analyze_trend(views: List[int], dates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze a single time series for trend direction, slope, R², p-value, and confidence.
    
    Args:
        views: List of integer view counts
        dates: Optional list of corresponding dates (YYYY-MM-DD)
        
    Returns:
        Dict with direction, slope, r_squared, p_value, confidence, total_growth_pct, etc.
    """
    num_periods = len(views)
    if num_periods == 0:
        return {
            "direction": "unknown",
            "slope": 0.0,
            "r_squared": 0.0,
            "p_value": 1.0,
            "confidence": "low",
            "total_growth_pct": 0.0,
            "avg_views": 0.0,
            "median_views": 0.0,
            "volatility": 0.0,
            "min_views": 0,
            "max_views": 0,
            "total_views": 0,
            "num_periods": 0,
            "note": "No data points provided"
        }
        
    arr = np.array(views, dtype=float)
    total_views = int(np.sum(arr))
    avg_views = float(np.mean(arr))
    median_views = float(np.median(arr))
    min_views = int(np.min(arr))
    max_views = int(np.max(arr))
    std_views = float(np.std(arr))
    volatility = round(std_views / avg_views, 3) if avg_views > 0 else 0.0
    
    # Handle single data point or flat line
    if num_periods < 2 or np.all(arr == arr[0]):
        return {
            "direction": "stable",
            "slope": 0.0,
            "r_squared": 0.0,
            "p_value": 1.0,
            "confidence": "low",
            "total_growth_pct": 0.0,
            "avg_views": round(avg_views, 1),
            "median_views": round(median_views, 1),
            "volatility": volatility,
            "min_views": min_views,
            "max_views": max_views,
            "total_views": total_views,
            "num_periods": num_periods,
            "note": "Insufficient variation or periods for regression"
        }
        
    # Linear regression: X is period index 0, 1, ..., N-1
    x = np.arange(num_periods)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, arr)
    r_squared = float(r_value ** 2) if not math.isnan(r_value) else 0.0
    p_val = float(p_value) if not math.isnan(p_value) else 1.0
    slope_val = float(slope) if not math.isnan(slope) else 0.0
    
    # Total growth calculation (smoothed over 3 periods if possible)
    if num_periods >= 6:
        start_avg = float(np.mean(arr[:3]))
        end_avg = float(np.mean(arr[-3:]))
        total_growth_pct = round(((end_avg - start_avg) / start_avg * 100.0), 2) if start_avg > 0 else 0.0
    else:
        start_val = float(arr[0])
        end_val = float(arr[-1])
        total_growth_pct = round(((end_val - start_val) / start_val * 100.0), 2) if start_val > 0 else 0.0

    # Direction assessment
    if slope_val > 0 and (p_val < 0.1 or total_growth_pct > 10.0):
        direction = "growing"
    elif slope_val < 0 and (p_val < 0.1 or total_growth_pct < -10.0):
        direction = "declining"
    else:
        direction = "stable"
        
    # Confidence level
    if r_squared > 0.6 and p_val < 0.05:
        confidence = "high"
    elif r_squared > 0.3 or p_val < 0.1:
        confidence = "medium"
    else:
        confidence = "low"
        
    log("ANALYSIS", f"Trend: {num_periods} periods | slope={slope_val:+.1f}/mo | R²={r_squared:.2f} | p={p_val:.4f} | {direction} ({confidence} conf) | growth={total_growth_pct:+.1f}%")
    
    return {
        "direction": direction,
        "slope": round(slope_val, 2),
        "r_squared": round(r_squared, 4),
        "p_value": round(p_val, 4),
        "confidence": confidence,
        "total_growth_pct": total_growth_pct,
        "avg_views": round(avg_views, 1),
        "median_views": round(median_views, 1),
        "volatility": volatility,
        "min_views": min_views,
        "max_views": max_views,
        "total_views": total_views,
        "num_periods": num_periods
    }


def detect_anomalies(views: List[int], dates: Optional[List[str]] = None, threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detect spikes and dips using Z-scores.
    
    Args:
        views: List of view counts
        dates: Optional list of date strings
        threshold: Standard deviation threshold (default 2.0)
    """
    if len(views) < 3:
        return []
        
    arr = np.array(views, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)
    if std == 0:
        return []
        
    z_scores = (arr - mean) / std
    anomalies = []
    for idx, z in enumerate(z_scores):
        if abs(z) >= threshold:
            anomaly_type = "spike" if z > 0 else "dip"
            d_str = dates[idx] if dates and idx < len(dates) else f"period_{idx}"
            anomalies.append({
                "index": idx,
                "date": d_str,
                "views": int(arr[idx]),
                "z_score": round(float(z), 2),
                "type": anomaly_type
            })
            
    log("ANALYSIS", f"Anomaly detection: found {len(anomalies)} anomalies (threshold={threshold}σ)")
    return anomalies


def detect_seasonality(views: List[int]) -> Dict[str, Any]:
    """
    Detect 12-month seasonality via lag-12 autocorrelation.
    Requires at least 14 data points.
    """
    if len(views) < 14:
        return {"has_seasonality": False, "period": None, "strength": 0.0}
        
    arr = np.array(views, dtype=float)
    mean = np.mean(arr)
    c0 = np.sum((arr - mean) ** 2)
    if c0 == 0:
        return {"has_seasonality": False, "period": None, "strength": 0.0}
        
    lag = 12
    c12 = np.sum((arr[:-lag] - mean) * (arr[lag:] - mean))
    r12 = round(float(c12 / c0), 3)
    has_seasonality = r12 >= 0.3
    
    log("ANALYSIS", f"Seasonality check: lag-12 autocorrelation = {r12} (seasonal: {has_seasonality})")
    return {
        "has_seasonality": has_seasonality,
        "period": 12 if has_seasonality else None,
        "strength": max(0.0, r12)
    }


def compare_trends(datasets: Dict[str, Union[List[int], List[Dict[str, Any]]]]) -> Dict[str, Any]:
    """
    Compare trends across multiple datasets (e.g., languages or topics).
    
    Args:
        datasets: Dict mapping label to either a list of view ints or list of {'date':..., 'views':...} dicts.
        
    Returns:
        Dict with individual analyses, correlations, ranking, anomalies, and recommendation.
    """
    individual: Dict[str, Any] = {}
    anomalies: Dict[str, Any] = {}
    clean_views: Dict[str, List[int]] = {}
    clean_dates: Dict[str, List[str]] = {}
    
    log("ANALYSIS", f"Comparing trends across {len(datasets)} datasets: {list(datasets.keys())}")
    
    for label, raw_data in datasets.items():
        v_list = []
        d_list = []
        if raw_data and isinstance(raw_data[0], dict):
            for item in raw_data:
                v_list.append(item.get("views", 0))
                d_list.append(item.get("date", ""))
        else:
            v_list = [int(v) for v in raw_data]
            
        clean_views[label] = v_list
        clean_dates[label] = d_list
        individual[label] = analyze_trend(v_list, d_list)
        anomalies[label] = detect_anomalies(v_list, d_list)
        
    # Correlations between pairs
    correlations: Dict[str, float] = {}
    labels = list(datasets.keys())
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            l1, l2 = labels[i], labels[j]
            v1, v2 = clean_views[l1], clean_views[l2]
            min_len = min(len(v1), len(v2))
            if min_len >= 3:
                a1 = np.array(v1[:min_len], dtype=float)
                a2 = np.array(v2[:min_len], dtype=float)
                if np.std(a1) > 0 and np.std(a2) > 0:
                    r = float(np.corrcoef(a1, a2)[0, 1])
                    if not math.isnan(r):
                        correlations[f"{l1}-{l2}"] = round(r, 3)
                        
    # Ranking by growth percentage descending
    ranking = sorted(labels, key=lambda l: individual[l].get("total_growth_pct", 0.0), reverse=True)
    
    # Recommendation text generation
    recommendation_lines = []
    growing = [l for l in ranking if individual[l]["direction"] == "growing"]
    high_conf = [l for l in growing if individual[l]["confidence"] == "high"]
    
    if growing:
        top = growing[0]
        growth = individual[top]["total_growth_pct"]
        conf = individual[top]["confidence"]
        avg = individual[top]["avg_views"]
        recommendation_lines.append(
            f"Strongest growth is in '{top}' (+{growth}%, {conf} confidence, ~{avg:,.0f} avg views/mo)."
        )
    else:
        recommendation_lines.append("No languages currently exhibit sustained growth in this time window.")
        
    if len(ranking) > 1:
        tail = ranking[-1]
        tail_growth = individual[tail]["total_growth_pct"]
        tail_dir = individual[tail]["direction"]
        recommendation_lines.append(f"Lowest relative momentum: '{tail}' ({tail_dir}, {tail_growth:+.1f}%).")
        
    rec_text = " ".join(recommendation_lines)
    log("ANALYSIS", f"Ranking: {ranking} | Recommendation: {rec_text}")
    
    return {
        "individual": individual,
        "correlations": correlations,
        "ranking": ranking,
        "anomalies": anomalies,
        "recommendation": rec_text
    }
