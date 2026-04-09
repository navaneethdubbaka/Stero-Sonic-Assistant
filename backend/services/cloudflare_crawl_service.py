"""
Cloudflare Browser Rendering /crawl API client.
Requires CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN (Browser Rendering - Edit).
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Optional

logger = logging.getLogger(__name__)

# Max characters of markdown/html to print per page in logs
_SCRAPE_LOG_PREVIEW_CHARS = 4000


class CloudflareCrawlError(Exception):
    pass


def _api_base(account_id: str) -> str:
    return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl"


def _request(
    method: str,
    url: str,
    token: str,
    body: Optional[dict] = None,
    timeout: int = 120,
) -> dict:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        raise CloudflareCrawlError(f"HTTP {e.code}: {err_body}") from e
    except urllib.error.URLError as e:
        raise CloudflareCrawlError(f"Request failed: {e}") from e

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CloudflareCrawlError(f"Invalid JSON response: {raw[:500]}") from e

    if not parsed.get("success"):
        errors = parsed.get("errors", [])
        raise CloudflareCrawlError(f"API error: {errors or parsed}")
    return parsed


def get_credentials() -> tuple[Optional[str], Optional[str]]:
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip() or None
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip() or None
    return account_id, token


def start_crawl(account_id: str, token: str, payload: dict) -> str:
    """POST crawl job; returns job id string."""
    url = _api_base(account_id)
    parsed = _request("POST", url, token, body=payload)
    result = parsed.get("result")
    if not result or not isinstance(result, str):
        raise CloudflareCrawlError(f"Unexpected start_crawl response: {parsed}")
    return result


def wait_for_job(
    account_id: str,
    token: str,
    job_id: str,
    poll_seconds: float = 5.0,
    max_wait_seconds: float = 180.0,
) -> dict:
    """Poll GET .../crawl/{job_id}?limit=1 until status is not running."""
    base = _api_base(account_id)
    url = f"{base}/{job_id}?limit=1"
    deadline = time.monotonic() + max_wait_seconds
    last: dict = {}
    while time.monotonic() < deadline:
        parsed = _request("GET", url, token)
        result = parsed.get("result")
        if not isinstance(result, dict):
            raise CloudflareCrawlError(f"Unexpected poll response: {parsed}")
        last = result
        status = result.get("status")
        if status != "running":
            return result
        time.sleep(poll_seconds)
    raise CloudflareCrawlError(
        f"Crawl job {job_id} still running after {max_wait_seconds}s"
    )


def fetch_all_records(
    account_id: str,
    token: str,
    job_id: str,
    max_total_chars: int = 2_000_000,
) -> List[dict]:
    """GET full job results, following cursor until done. Caps aggregated text size."""
    base = _api_base(account_id)
    cursor: Optional[str] = None
    all_records: List[dict] = []
    total_chars = 0

    while True:
        q = f"{base}/{job_id}"
        params: List[str] = []
        if cursor:
            params.append("cursor=" + urllib.parse.quote(cursor, safe=""))
        if params:
            q += "?" + "&".join(params)
        parsed = _request("GET", q, token)
        result = parsed.get("result")
        if not isinstance(result, dict):
            raise CloudflareCrawlError(f"Unexpected fetch response: {parsed}")

        records = result.get("records") or []
        if not isinstance(records, list):
            records = []

        for rec in records:
            if not isinstance(rec, dict):
                continue
            for key in ("markdown", "html", "json"):
                v = rec.get(key)
                if isinstance(v, str):
                    total_chars += len(v)
            all_records.append(rec)
            if total_chars >= max_total_chars:
                return all_records

        next_cursor = result.get("cursor")
        if not next_cursor:
            break
        cursor = str(next_cursor)

    return all_records


def crawl_single_page(
    url: str,
    *,
    limit: int = 1,
    render: bool = False,
    formats: Optional[List[str]] = None,
    crawl_purposes: Optional[List[str]] = None,
    poll_seconds: float = 5.0,
    max_wait_seconds: float = 120.0,
) -> dict:
    """
    Start a crawl job for one (or few) page(s), wait, fetch records.
    Returns a dict safe to stringify in tools (ok, url, markdown, errors, ...).
    """
    account_id, token = get_credentials()
    if not account_id or not token:
        logger.warning(
            "[cloudflare_crawl] skip — missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN for url=%s",
            url,
        )
        return {
            "ok": False,
            "url": url,
            "error": "Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN",
        }

    if formats is None:
        formats = ["markdown"]
    if crawl_purposes is None:
        crawl_purposes = ["search", "ai-input"]

    payload: dict = {
        "url": url,
        "limit": max(1, min(limit, 100_000)),
        "formats": formats,
        "render": render,
        "crawlPurposes": crawl_purposes,
    }

    try:
        job_id = start_crawl(account_id, token, payload)
        logger.info(
            "[cloudflare_crawl] job started job_id=%s url=%s limit=%s render=%s formats=%s",
            job_id,
            url,
            payload.get("limit"),
            render,
            formats,
        )
        summary = wait_for_job(
            account_id,
            token,
            job_id,
            poll_seconds=poll_seconds,
            max_wait_seconds=max_wait_seconds,
        )
        job_status = summary.get("status", "unknown")
        logger.info(
            "[cloudflare_crawl] job finished job_id=%s url=%s status=%s browser_seconds=%s",
            job_id,
            url,
            job_status,
            summary.get("browserSecondsUsed"),
        )
    except CloudflareCrawlError as e:
        logger.error("[cloudflare_crawl] job failed url=%s error=%s", url, e)
        return {"ok": False, "url": url, "error": str(e)}

    out: dict = {
        "ok": job_status == "completed",
        "url": url,
        "job_status": job_status,
        "record_status": None,
        "title": None,
        "markdown": None,
        "html": None,
        "error": None,
    }

    if job_status != "completed":
        out["error"] = f"Crawl job ended with status: {job_status}"
        logger.warning(
            "[cloudflare_crawl] incomplete job_id=%s url=%s job_status=%s",
            job_id,
            url,
            job_status,
        )
        return out

    try:
        records = fetch_all_records(account_id, token, job_id)
    except CloudflareCrawlError as e:
        out["ok"] = False
        out["error"] = str(e)
        logger.error("[cloudflare_crawl] fetch records failed job_id=%s url=%s error=%s", job_id, url, e)
        return out

    if not records:
        out["ok"] = False
        out["error"] = "No records in completed job"
        logger.warning("[cloudflare_crawl] no records job_id=%s url=%s", job_id, url)
        return out

    logger.info("[cloudflare_crawl] fetched %d record(s) job_id=%s url=%s", len(records), job_id, url)

    md_chunks: List[str] = []
    html_chunks: List[str] = []
    first_title: Optional[str] = None
    worst_status: Optional[str] = None

    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            continue
        st = rec.get("status")
        if st and st != "completed":
            worst_status = st
        meta = rec.get("metadata") if isinstance(rec.get("metadata"), dict) else {}
        rec_url = meta.get("url") or url
        http_status = meta.get("status")
        if first_title is None and meta.get("title"):
            first_title = str(meta.get("title"))
        logger.info(
            "[cloudflare_crawl] record[%d] page_url=%s record_status=%s http_status=%s title=%r",
            idx,
            rec_url,
            st,
            http_status,
            (meta.get("title") or "")[:120],
        )
        m = rec.get("markdown")
        if isinstance(m, str) and m.strip():
            md_chunks.append(m.strip())
            prev = m.strip()[:_SCRAPE_LOG_PREVIEW_CHARS]
            if len(m.strip()) > _SCRAPE_LOG_PREVIEW_CHARS:
                prev += "\n... [truncated for log]"
            logger.info("[cloudflare_crawl] record[%d] markdown preview:\n%s", idx, prev)
        h = rec.get("html")
        if isinstance(h, str) and h.strip():
            html_chunks.append(h.strip())
            if not m or not str(m).strip():
                hprev = h.strip()[:_SCRAPE_LOG_PREVIEW_CHARS]
                if len(h.strip()) > _SCRAPE_LOG_PREVIEW_CHARS:
                    hprev += "\n... [truncated for log]"
                logger.info("[cloudflare_crawl] record[%d] html preview:\n%s", idx, hprev)

    out["title"] = first_title
    out["markdown"] = "\n\n---\n\n".join(md_chunks) if md_chunks else None
    out["html"] = "\n\n---\n\n".join(html_chunks) if html_chunks else None
    out["record_status"] = worst_status or "completed"

    if not out["markdown"] and not out["html"]:
        out["ok"] = False
        out["error"] = worst_status or "No text content in crawl records"
        logger.warning(
            "[cloudflare_crawl] no text content job_id=%s url=%s worst_status=%s",
            job_id,
            url,
            worst_status,
        )
        return out

    if worst_status and worst_status != "completed":
        out["ok"] = False
        out["error"] = f"Some pages had status: {worst_status}"
        logger.warning(
            "[cloudflare_crawl] partial failure job_id=%s url=%s worst_status=%s",
            job_id,
            url,
            worst_status,
        )

    if out.get("ok"):
        logger.info(
            "[cloudflare_crawl] crawl_ok url=%s title=%r markdown_chars=%s html_chars=%s",
            url,
            out.get("title"),
            len(out["markdown"] or ""),
            len(out["html"] or ""),
        )
    else:
        logger.warning(
            "[cloudflare_crawl] crawl_finished_with_issues url=%s error=%r markdown_chars=%s",
            url,
            out.get("error"),
            len(out["markdown"] or ""),
        )
    return out
