"""Has the consumer press already written up these studies?

Answers the one question that decides whether a pitch is still open, and feeds
the outlet suggestions so a story is never pitched to the publication that just
ran it.

Ported from senior-research-digest with the study key changed from PMID to the
OpenAlex work ID; the matching logic and both time budgets are unchanged.

Google News ranks by topical relevance, so a query about a grip-strength study
returns anything about grip strength. Results are therefore filtered on
headline overlap with the study title -- the same guard
agingwire-research-intelligence needed after its first live run reported 12 of
13 items as widely covered.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

BASE = "https://serpapi.com/search"
TIMEOUT = 25
RETRIES = 2
RETRY_STATUS = {429, 500, 502, 503, 504}
PAUSE_SECONDS = 0.4        # the SerpAPI quota is shared with other repos
DEFAULT_DAYS_BACK = 60     # overridden by digest_config.json's days_back
MAX_QUERY_WORDS = 10

# Every study in the digest is checked, not just the first few, but a runaway
# digest should not be able to drain a shared quota in one run.
MAX_CHECKS_PER_RUN = 40

# A per-request timeout bounds one call; it does not bound this loop. At 40
# studies x (RETRIES + 1) attempts x TIMEOUT plus backoff, the worst case is
# about 54 minutes -- inside a 20-minute pipeline step. That is not theoretical:
# it is what killed the 2026-09-06 run. Coverage went from free to fatal the day
# SERPAPI_API_KEY was added, because until then this returned immediately.
#
# So the loop gets its own wall clock. When the budget is spent the remaining
# studies are reported as skipped, with a reason, exactly like a spent quota --
# a partial coverage check is useful, a dead pipeline is not. Coverage is the
# least important stage here and must never be the one that costs the digest.
#
# The same bug was fixed in trending-content (MEA-55) and new-scientist-story-
# ideas (MEA-57); those repos are separate codebases, so the fix did not travel.
MAX_WALL_SECONDS = 240

CACHE_PATH = Path(__file__).parent.parent / "state" / "coverage_cache.json"
# Coverage is not static -- an unreported study can be picked up next week. A
# study is written up once (screening drops anything covered before), so the
# cache matters less here than in senior-research-digest; it still saves the
# lookups when a failed run is re-run the same day.
CACHE_TTL_DAYS = 14

STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "by",
    "from", "at", "as", "is", "are", "was", "were", "be", "this", "that", "new",
    "may", "can", "could", "study", "studies", "research", "how", "why", "when",
    "what", "effect", "effects", "role", "impact", "your", "you", "more", "less",
}
JACCARD_FLOOR = 0.18
SHARED_MIN = 3
SHARED_RATIO = 0.35


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(w) > 2 and w not in STOP}


def title_similar(left: str, right: str) -> bool:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return False
    shared = a & b
    if len(shared) / len(a | b) >= JACCARD_FLOOR:
        return True
    return len(shared) >= SHARED_MIN and len(shared) / min(len(a), len(b)) >= SHARED_RATIO


def build_query(title: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", re.sub(r"\([^)]*\)", " ", title or ""))
    words = [w for w in cleaned.split() if len(w) > 2 and w.lower() not in STOP]
    return " ".join(words[:MAX_QUERY_WORDS])


def _serp(params: dict) -> dict | None:
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if not key:
        return None
    url = BASE + "?" + urllib.parse.urlencode({**params, "api_key": key})
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
        except TimeoutError:
            if attempt < RETRIES:
                time.sleep(2 * (attempt + 1))
                continue
            return None
        except urllib.error.HTTPError as exc:
            # A rate limit or a bad gateway is worth another try; a 4xx is not.
            if exc.code in RETRY_STATUS and attempt < RETRIES:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  SerpAPI HTTP {exc.code}", file=sys.stderr)
            return None
        except urllib.error.URLError as exc:
            if attempt < RETRIES:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  SerpAPI unreachable: {str(exc.reason)[:100]}", file=sys.stderr)
            return None
        except Exception as exc:
            print(f"  SerpAPI error: {str(exc)[:120]}", file=sys.stderr)
            return None
        # SerpAPI answers 200 with an {"error": ...} body for a spent quota --
        # and also, in the same shape, for a search that simply found nothing.
        # The second is the best answer this module can get (nobody has covered
        # the study), and treating it as a failure filed every unreported study
        # as "skipped": 11 of 22 on the 2026-09-13 run, all of them this
        # message. Only a real failure returns None.
        if isinstance(data, dict) and data.get("error"):
            if _NO_RESULTS.search(str(data["error"])):
                return {**data, "news_results": []}
            print(f"  SerpAPI: {str(data['error'])[:120]}", file=sys.stderr)
            return None
        return data
    return None


_NO_RESULTS = re.compile(r"hasn't returned any results|returned no results|no results", re.I)


def check_study(title: str, days_back: int = DEFAULT_DAYS_BACK) -> dict | None:
    query = build_query(title)
    if not query:
        return None
    data = _serp({"engine": "google_news", "q": f"{query} when:{days_back}d",
                  "gl": "us", "hl": "en"})
    if data is None:
        return None
    outlets, samples, returned = [], [], 0
    for article in (data.get("news_results") or [])[:20]:
        headline = (article.get("title") or "").strip()
        link = (article.get("link") or "").strip()
        if not headline or not link:
            continue
        returned += 1
        if not title_similar(title, headline):
            continue
        name = ((article.get("source") or {}).get("name")
                or urlparse(link).netloc.lower().removeprefix("www.")).strip()
        if name and name not in outlets:
            outlets.append(name)
            samples.append({"title": headline[:200], "outlet": name, "link": link})
    return {"query": query, "returned": returned, "outlets": outlets,
            "articles": samples[:3],
            "state": "unreported" if not outlets
                     else "lightly_reported" if len(outlets) <= 2 else "widely_reported"}


def _load_cache(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=CACHE_TTL_DAYS)
    fresh = {}
    for work_id, entry in (raw.get("studies") or {}).items():
        try:
            seen = datetime.fromisoformat(entry["checked_at"])
        except (KeyError, TypeError, ValueError):
            continue
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        if seen >= cutoff:
            fresh[work_id] = entry
    return fresh


def _save_cache(path: Path, studies: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"studies": studies}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"  coverage cache not written: {exc}", file=sys.stderr)


def check_digest(
    studies,
    days_back: int = DEFAULT_DAYS_BACK,
    cache_path: Path | None = CACHE_PATH,
    limit: int = MAX_CHECKS_PER_RUN,
    wall_seconds: float = MAX_WALL_SECONDS,
) -> dict:
    """Check every study and collect the outlets already reporting them.

    Accepts either `[(work_id, title), ...]` or a plain list of titles. Results
    are cached by work ID.
    """
    if not os.environ.get("SERPAPI_API_KEY", "").strip():
        return {"checked": 0, "cached": 0, "skipped": 0,
                "skipped_reason": "SERPAPI_API_KEY is not set",
                "outlets": set(), "by_study": {}, "by_work": {}}

    pairs = [s if isinstance(s, (tuple, list)) else ("", s) for s in studies]
    cache = _load_cache(cache_path) if cache_path else {}

    checked = cached_hits = skipped = 0
    stored = False
    out_of_time = False
    started = time.monotonic()
    covered, by_study, by_work = set(), {}, {}

    for work_id, raw in pairs:
        title = (raw or "").strip()
        if not title:
            continue

        entry = cache.get(work_id) if work_id else None
        if entry and entry.get("result"):
            result = entry["result"]
            cached_hits += 1
        elif checked >= limit or time.monotonic() - started > wall_seconds:
            # Out of budget for this run rather than out of studies. Recorded so
            # the dashboard can say the check was partial instead of implying
            # these studies came back clean. Two budgets now: the shared SerpAPI
            # quota, and the wall clock -- a slow or rate-limited SerpAPI spends
            # the second long before the first.
            out_of_time = out_of_time or checked < limit
            skipped += 1
            continue
        else:
            if checked:
                time.sleep(PAUSE_SECONDS)
            result = check_study(title, days_back=days_back)
            if result is None:
                skipped += 1
                continue
            checked += 1
            if work_id:
                cache[work_id] = {
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "result": result,
                }
                stored = True

        by_study[title] = result
        if work_id:
            by_work[work_id] = result
        covered.update(result["outlets"])

    if cache_path and stored:
        _save_cache(cache_path, cache)

    result = {"checked": checked, "cached": cached_hits, "skipped": skipped,
              "outlets": covered, "by_study": by_study, "by_work": by_work}
    if out_of_time:
        # Not a skipped_reason: the check did run and what it found is real.
        # This says the remainder was abandoned on time, so the dashboard does
        # not read silence as "no outlet has covered these".
        result["partial_reason"] = (
            f"coverage stopped after {wall_seconds:.0f}s; "
            f"{skipped} study(ies) unchecked"
        )
    return result
