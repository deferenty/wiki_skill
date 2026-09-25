"""Wikimedia API client for wiki-trends."""
import time
import urllib.parse
from typing import Any, Dict, List, Optional
import requests

from .logger import log

USER_AGENT = "WikiTrends/1.0 (https://github.com/wiki-trends; agent-skill@example.com) python-requests"
PAGEVIEWS_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
RATE_LIMIT_DELAY = 0.1  # 100ms between calls
MAX_RETRIES = 3


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def normalize_date(date_str: str) -> str:
    """Normalize date strings (YYYYMMDD, YYYY-MM-DD, YYYYMMDD00) to YYYYMMDD00."""
    cleaned = date_str.replace("-", "").strip()
    if len(cleaned) == 8:
        return cleaned + "00"
    if len(cleaned) == 10:
        return cleaned
    raise ValueError(f"Invalid date format: '{date_str}'. Expected YYYYMMDD or YYYY-MM-DD.")


def format_timestamp(timestamp_str: str) -> str:
    """Format API timestamp (YYYYMMDD00) to YYYY-MM-DD."""
    if len(timestamp_str) >= 8:
        return f"{timestamp_str[0:4]}-{timestamp_str[4:6]}-{timestamp_str[6:8]}"
    return timestamp_str


def _request_with_retry(session: requests.Session, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    """Execute GET request with rate limiting and exponential backoff retry."""
    time.sleep(RATE_LIMIT_DELAY)
    
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        log("API", f"GET {url}" + (f" with params {params}" if params else ""))
        start_time = time.time()
        try:
            resp = session.get(url, params=params, timeout=15)
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                log("API", f"Response: 200 OK ({elapsed:.3f}s)")
                return resp
            elif resp.status_code == 404:
                log("API", f"Response: 404 Not Found ({elapsed:.3f}s) — Article not found or no views in period")
                return resp
            elif resp.status_code == 429:
                wait_time = 2.0 ** attempt
                log("API", f"Response: 429 Too Many Requests ({elapsed:.3f}s) — Retrying in {wait_time:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait_time)
                continue
            elif 500 <= resp.status_code < 600:
                wait_time = 1.5 ** attempt
                log("API", f"Response: {resp.status_code} Server Error ({elapsed:.3f}s) — Retrying in {wait_time:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait_time)
                continue
            else:
                log("API", f"Response: {resp.status_code} ({elapsed:.3f}s) — Error: {resp.text[:200]}")
                resp.raise_for_status()
                return resp
        except requests.RequestException as e:
            last_exc = e
            elapsed = time.time() - start_time
            if attempt < MAX_RETRIES:
                wait_time = 2.0 ** attempt
                log("API", f"Request exception ({elapsed:.3f}s): {e} — Retrying in {wait_time:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                log("ERROR", f"Request failed after {MAX_RETRIES} attempts: {e}")
                raise
                
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} retries")


def resolve_article(topic: str, source_lang: str = "en", target_langs: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Find article titles across languages using MediaWiki action=query and langlinks.
    Falls back to action=query&list=search if exact title lookup fails.
    
    Args:
        topic: Article title or search query
        source_lang: Source Wikipedia language (default: 'en')
        target_langs: List of target languages (e.g., ['pl', 'cs', 'uk'])
        
    Returns:
        Dict with 'source': {'lang': ..., 'article': ...}, 'resolved': {lang: title}, 'not_found': [langs]
    """
    target_langs = target_langs or []
    session = _get_session()
    base_api = f"https://{source_lang}.wikipedia.org/w/api.php"
    
    clean_topic = topic.strip().replace(" ", "_")
    log("RESOLVE", f"Looking up '{topic}' in {source_lang}.wikipedia...")
    
    # 1. First attempt: direct title lookup with langlinks
    params = {
        "action": "query",
        "titles": clean_topic,
        "prop": "langlinks",
        "lllimit": "500",
        "format": "json",
        "redirects": "1"
    }
    resp = _request_with_retry(session, base_api, params=params)
    data = resp.json() if resp.status_code == 200 else {}
    
    pages = data.get("query", {}).get("pages", {})
    resolved_source_title = None
    langlinks = {}
    
    for page_id, page_info in pages.items():
        if page_id != "-1":
            resolved_source_title = page_info.get("title", clean_topic).replace(" ", "_")
            for ll in page_info.get("langlinks", []):
                lang = ll.get("lang")
                title = ll.get("*", "").replace(" ", "_")
                if lang and title:
                    langlinks[lang] = title
            break
            
    # 2. Fallback: Search API if page not found
    if not resolved_source_title:
        log("RESOLVE", f"Direct title '{clean_topic}' not found on {source_lang}.wikipedia, searching...")
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": topic,
            "srlimit": "1",
            "format": "json"
        }
        search_resp = _request_with_retry(session, base_api, params=search_params)
        search_data = search_resp.json() if search_resp.status_code == 200 else {}
        search_results = search_data.get("query", {}).get("search", [])
        
        if search_results:
            top_title = search_results[0]["title"]
            log("RESOLVE", f"Found closest match via search: '{top_title}'. Querying langlinks...")
            # Query langlinks for top search result
            params["titles"] = top_title
            resp = _request_with_retry(session, base_api, params=params)
            data = resp.json() if resp.status_code == 200 else {}
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1":
                    resolved_source_title = page_info.get("title", top_title).replace(" ", "_")
                    for ll in page_info.get("langlinks", []):
                        lang = ll.get("lang")
                        title = ll.get("*", "").replace(" ", "_")
                        if lang and title:
                            langlinks[lang] = title
                    break
        else:
            log("RESOLVE", f"No matching articles found for topic '{topic}' on {source_lang}.wikipedia")
            
    if not resolved_source_title:
        resolved_source_title = clean_topic

    resolved = {}
    not_found = []
    
    # Include source language if asked or by default
    if source_lang in target_langs or not target_langs:
        resolved[source_lang] = resolved_source_title

    for target in target_langs:
        if target == source_lang:
            resolved[target] = resolved_source_title
        elif target in langlinks:
            resolved[target] = langlinks[target]
        else:
            not_found.append(target)
            
    log("RESOLVE", f"Resolution complete: resolved={resolved}, not_found={not_found}")
    return {
        "source": {"lang": source_lang, "article": resolved_source_title},
        "resolved": resolved,
        "not_found": not_found
    }


def fetch_pageviews(article: str, lang: str, start: str, end: str, granularity: str = "monthly") -> List[Dict[str, Any]]:
    """
    Fetch pageview metrics for a single article in a single language.
    
    Args:
        article: Article title (e.g. 'Post_przerywany' or 'Intermittent fasting')
        lang: Language code (e.g. 'pl')
        start: Start date (YYYYMMDD or YYYY-MM-DD)
        end: End date (YYYYMMDD or YYYY-MM-DD)
        granularity: 'monthly' or 'daily'
        
    Returns:
        List of {'date': 'YYYY-MM-DD', 'views': int} sorted chronologically.
    """
    session = _get_session()
    start_norm = normalize_date(start)
    end_norm = normalize_date(end)
    clean_article = article.strip().replace(" ", "_")
    encoded_article = urllib.parse.quote(clean_article, safe="")
    project = f"{lang}.wikipedia"
    
    url = f"{PAGEVIEWS_BASE}/{project}/all-access/user/{encoded_article}/{granularity}/{start_norm}/{end_norm}"
    log("FETCH", f"Fetching {project}/{clean_article} ({granularity}, {start_norm} to {end_norm})")
    
    resp = _request_with_retry(session, url)
    if resp.status_code == 404:
        log("FETCH", f"No data found for {project}/{clean_article} (404)")
        return []
    
    data = resp.json()
    items = data.get("items", [])
    result = []
    for item in items:
        ts = item.get("timestamp", "")
        formatted_date = format_timestamp(ts)
        views = item.get("views", 0)
        result.append({"date": formatted_date, "views": views})
        
    result.sort(key=lambda x: x["date"])
    log("FETCH", f"Received {len(result)} data points for {project}/{clean_article}")
    return result


def fetch_multi(articles: Dict[str, str], start: str, end: str, granularity: str = "monthly") -> Dict[str, Any]:
    """
    Fetch pageviews for multiple articles across different languages.
    
    Args:
        articles: Dict mapping lang code to article title, e.g. {'pl': 'Post_przerywany', 'cs': 'Intermitentní_hladovění'}
        start: Start date
        end: End date
        granularity: 'monthly' or 'daily'
        
    Returns:
        Dict with 'query', 'data', and 'metadata'.
    """
    start_time = time.time()
    results: Dict[str, List[Dict[str, Any]]] = {}
    data_points: Dict[str, int] = {}
    
    log("FETCH", f"Starting multi-fetch for {len(articles)} articles ({start} to {end})...")
    
    for lang, title in articles.items():
        if not title:
            log("FETCH", f"Skipping language '{lang}' (no article title provided)")
            results[lang] = []
            data_points[lang] = 0
            continue
        pts = fetch_pageviews(title, lang, start, end, granularity=granularity)
        results[lang] = pts
        data_points[lang] = len(pts)
        
    total_time = time.time() - start_time
    log("FETCH", f"Multi-fetch finished in {total_time:.2f}s. Data points: {data_points}")
    
    return {
        "query": {
            "articles": articles,
            "start": start,
            "end": end,
            "granularity": granularity
        },
        "data": results,
        "metadata": {
            "total_requests": len(articles),
            "total_time_sec": round(total_time, 2),
            "data_points": data_points
        }
    }
