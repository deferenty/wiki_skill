# Wikimedia Pageviews API Reference

## Base URL
`https://wikimedia.org/api/rest_v1`

## Endpoints Used

### 1. Per-Article Pageviews
`GET /metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}`

**Parameters:**
| Param | Values | Notes |
|---|---|---|
| `project` | `{lang}.wikipedia` | e.g., `en.wikipedia`, `uk.wikipedia` (no `.org`!) |
| `access` | `all-access` | desktop + mobile web + mobile app |
| `agent` | `user` | filters out automated bots / spiders |
| `article` | URL-encoded title | Spaces must be underscores (`_`) |
| `granularity` | `daily` or `monthly` | `monthly` recommended for multi-year trends |
| `start` | `YYYYMMDD00` | Note trailing `00` for timestamp hours |
| `end` | `YYYYMMDD00` | Note trailing `00` for timestamp hours |

**Response Format:**
```json
{
  "items": [
    {
      "project": "pl.wikipedia",
      "article": "Post_przerywany",
      "granularity": "monthly",
      "timestamp": "2024010100",
      "access": "all-access",
      "agent": "user",
      "views": 15234
    }
  ]
}
```

### 2. Article Title Resolution (MediaWiki API)
Base URL: `https://{lang}.wikipedia.org/w/api.php`

**Cross-language title lookup (`langlinks`):**
- `action=query`
- `titles={Source_Article_Title}`
- `prop=langlinks`
- `lllimit=500`
- `format=json`

**Article title search fallback (`search`):**
- `action=query`
- `list=search`
- `srsearch={search_term}`
- `srlimit=5`
- `format=json`

## Required Headers
- `User-Agent`: Wikimedia requires an identifying User-Agent policy.
  Format: `WikiTrends/1.0 (https://github.com/wiki-trends; contact@example.com) python-requests`

## Rate Limits & Best Practices
- Authentication: None required for public endpoints.
- Rate pacing: Add 100ms pause between sequential requests.
- Exponential backoff: Retry on HTTP 429 (Too Many Requests) or 5xx server errors up to 3 times.

## Gotchas & Important Rules
- Project is `{lang}.wikipedia`, NEVER `{lang}.wikipedia.org`.
- Article titles in URLs must use underscores (`_`), not spaces.
- Titles are case-sensitive except for the initial letter.
- Dates require trailing `00`: pass `2024010100`, not `20240101`.
- The API returns HTTP 404 for articles that exist but had zero views in that window (or do not exist); treat 404 as 0 views / empty dataset rather than an unrecoverable failure.
