"""
Extract top organic search URLs (and optional titles/snippets) for web research.
Primary: Selenium + Google SERP. Fallback: DuckDuckGo HTML (no JS) if Google yields nothing or engine is duckduckgo.

ChromeDriver on Windows: Prefer Selenium 4.6+ built-in manager instead of webdriver-manager first, because a bad
cached chromedriver from webdriver-manager triggers WinError 193 (%1 is not a valid Win32 application).

Env:
  WEB_RESEARCH_HEADLESS — if unset: false on Windows (visible Chrome, best for Google), true on other OS
  WEB_RESEARCH_ENGINE — "google" (default) or "duckduckgo"
  CHROMEDRIVER_PATH — optional explicit path to chromedriver.exe (used first if set)
  CHROME_BINARY — optional path to chrome.exe; otherwise common Windows install paths are auto-detected
  WEB_RESEARCH_CHROME_VERBOSE — set to "true" to show Chromedriver logs (default: quiet)

Console noise (harmless):
  "DevTools listening on ws://..." — Chrome/Chromedriver always opens a debug port; not an error.
  "GetGpuDriverOverlayInfo: Failed to retrieve video device" — common Windows GPU overlay message; safe to ignore.
"""

from __future__ import annotations

import html as html_lib
import logging
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

# Host substrings to skip when collecting organic links (wrapped or direct).
_SKIP_HOST_HINTS = (
    "google.",
    "gstatic.",
    "googleusercontent.",
    "webcache.",
    "blogger.com",
    "schema.org",
)

_DD_RESULT_LINK = re.compile(
    r'class="result__a"[^>]*href="([^"]+)"',
    re.IGNORECASE,
)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


def _default_headless() -> bool:
    """Visible Chrome on Windows avoids many Google headless/consent issues; servers can set WEB_RESEARCH_HEADLESS=true."""
    v = os.getenv("WEB_RESEARCH_HEADLESS", "").strip().lower()
    if v:
        return v in ("1", "true", "yes", "on")
    return sys.platform != "win32"


def _find_installed_chrome_executable() -> Optional[str]:
    """
    Resolve chrome.exe: CHROME_BINARY, then standard Windows locations, then common env (LOCALAPPDATA).
    """
    explicit = os.getenv("CHROME_BINARY", "").strip()
    if explicit and os.path.isfile(explicit):
        return explicit

    candidates: List[str] = []
    if sys.platform == "win32":
        pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        pfx86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        local = os.environ.get("LOCALAPPDATA", "")
        candidates.extend(
            [
                os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(pfx86, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
            ]
        )
    elif sys.platform == "darwin":
        candidates.append(
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
    else:
        candidates.extend(
            [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ]
        )

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def _apply_chrome_binary(options: ChromeOptions) -> None:
    path = _find_installed_chrome_executable()
    if path:
        options.binary_location = path
        logger.info("Web research using Chrome at: %s", path)
    else:
        logger.warning(
            "Chrome executable not found; set CHROME_BINARY. Selenium may fall back to bundled Chromium."
        )


def _dismiss_google_consent(driver) -> None:
    """Best-effort cookie / consent dialogs that block the SERP."""
    selectors = [
        (By.XPATH, "//button[contains(., 'Accept all')]"),
        (By.XPATH, "//button[contains(., 'Accept all cookies')]"),
        (By.XPATH, "//div[@role='none']//button[contains(., 'Accept')]"),
        (By.CSS_SELECTOR, "button#L2AGLb"),
        (By.CSS_SELECTOR, "form[action*='consent'] button"),
    ]
    for by, sel in selectors:
        try:
            el = driver.find_element(by, sel)
            if el.is_displayed():
                el.click()
                time.sleep(0.5)
                return
        except Exception:
            continue


def _unwrap_google_redirect(href: str) -> str:
    """Turn Google redirect URLs into the target URL when possible."""
    if not href:
        return href
    try:
        if href.startswith("/url?"):
            href = "https://www.google.com" + href
        parsed = urlparse(href)
        if "google." in parsed.netloc and parsed.path == "/url":
            qs = urllib.parse.parse_qs(parsed.query)
            q = (qs.get("q") or [None])[0]
            if q:
                return urllib.parse.unquote(q)
    except Exception:
        pass
    return href


def _is_usable_http_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    if not host:
        return False
    for hint in _SKIP_HOST_HINTS:
        if hint in host:
            return False
    return True


def _chrome_service(executable_path: Optional[str] = None) -> ChromeService:
    """Chromedriver service; stderr silenced by default (WEB_RESEARCH_CHROME_VERBOSE=true for debugging)."""
    if _env_bool("WEB_RESEARCH_CHROME_VERBOSE", False):
        if executable_path:
            return ChromeService(executable_path=executable_path)
        return ChromeService()
    kwargs: dict = {"log_output": subprocess.DEVNULL}
    if executable_path:
        kwargs["executable_path"] = executable_path
    return ChromeService(**kwargs)


def _create_chrome_driver(chrome_options: ChromeOptions):
    """
    Start Chrome with a driver that matches this Windows install.
    Order: CHROMEDRIVER_PATH -> Selenium Manager (no webdriver-manager) -> webdriver-manager fallback.
    """
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "").strip()
    errors: List[str] = []

    if chromedriver_path and os.path.isfile(chromedriver_path):
        try:
            return webdriver.Chrome(
                service=_chrome_service(chromedriver_path),
                options=chrome_options,
            )
        except OSError as e:
            errors.append(f"CHROMEDRIVER_PATH: {e}")
        except Exception as e:
            errors.append(f"CHROMEDRIVER_PATH: {e}")

    try:
        return webdriver.Chrome(
            service=_chrome_service(),
            options=chrome_options,
        )
    except OSError as e:
        errors.append(f"Selenium Manager: {e}")
    except Exception as e:
        errors.append(f"Selenium Manager: {e}")

    try:
        driver_path = ChromeDriverManager().install()
        return webdriver.Chrome(
            service=_chrome_service(driver_path),
            options=chrome_options,
        )
    except Exception as e:
        errors.append(f"webdriver-manager: {e}")

    raise OSError(
        "Could not start Chrome WebDriver (WinError 193 often means wrong chromedriver.exe). "
        + "Install Google Chrome, set CHROMEDRIVER_PATH to a matching ChromeDriver from "
        + "https://googlechromelabs.github.io/chrome-for-testing/ , or use WEB_RESEARCH_ENGINE=duckduckgo. "
        + "Details: "
        + "; ".join(errors)
    )


def _google_serp_results(query: str, num_results: int, headless: bool) -> List[Dict[str, str]]:
    """Return list of {url, title, snippet} using Selenium on Google (your installed Chrome when found)."""
    chrome_options = ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)

    _apply_chrome_binary(chrome_options)

    q = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={q}&num=10&hl=en"

    driver = None
    out: List[Dict[str, str]] = []
    seen: Set[str] = set()

    try:
        driver = _create_chrome_driver(chrome_options)
        driver.set_page_load_timeout(45)
        driver.get(url)
        _dismiss_google_consent(driver)

        result_locator = (
            By.CSS_SELECTOR,
            "#rso, #search, #center_col, #main, div[role='main'], form[action='/search']",
        )
        WebDriverWait(driver, 25).until(EC.presence_of_element_located(result_locator))
        time.sleep(1.2)

        anchors = driver.find_elements(
            By.CSS_SELECTOR,
            "#rso a[href], div[role='main'] a[href], #search a[href], #center_col a[href]",
        )
        for a in anchors:
            if len(out) >= num_results:
                break
            try:
                raw_href = a.get_attribute("href") or ""
            except Exception:
                continue
            target = _unwrap_google_redirect(raw_href)
            if not _is_usable_http_url(target):
                continue
            if target in seen:
                continue
            seen.add(target)
            title = ""
            try:
                title = (a.text or "").strip()
            except Exception:
                pass
            out.append({"url": target, "title": title, "snippet": ""})

    except Exception as e:
        logger.warning(
            "Google SERP via Selenium failed, will use DuckDuckGo if needed: %s: %s",
            type(e).__name__,
            e,
            exc_info=logger.isEnabledFor(logging.DEBUG),
        )

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    if out:
        logger.info(
            "[web_search] Google Selenium SERP query=%r count=%d urls=%s",
            query,
            len(out),
            [x["url"] for x in out],
        )
    return out


def _duckduckgo_html_results(query: str, num_results: int) -> List[Dict[str, str]]:
    """Fetch DuckDuckGo HTML results without Selenium (fallback)."""
    q = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("[web_search] DuckDuckGo HTML fetch failed query=%r: %s", query, e)
        return []

    out: List[Dict[str, str]] = []
    seen: Set[str] = set()
    for m in _DD_RESULT_LINK.finditer(body):
        if len(out) >= num_results:
            break
        href = html_lib.unescape(m.group(1))
        if not _is_usable_http_url(href):
            continue
        if href in seen:
            continue
        seen.add(href)
        out.append({"url": href, "title": "", "snippet": ""})

    if out:
        logger.info(
            "[web_search] DuckDuckGo HTML query=%r count=%d urls=%s",
            query,
            len(out),
            [x["url"] for x in out],
        )
    return out


def fetch_top_search_results(query: str, num_results: int = 5) -> Dict:
    """
    Return {"success": bool, "results": [{url, title, snippet}, ...], "error": str|None, "source": str}
    """
    query = (query or "").strip()
    if not query:
        logger.warning("[web_search] rejected empty query")
        return {"success": False, "results": [], "error": "Empty query", "source": ""}

    num_results = max(1, min(int(num_results), 10))
    headless = _default_headless()
    engine = os.getenv("WEB_RESEARCH_ENGINE", "google").strip().lower()

    results: List[Dict[str, str]] = []
    source = ""

    logger.info(
        "[web_search] fetch_top_search_results query=%r num_results=%s engine=%s headless=%s",
        query,
        num_results,
        engine,
        headless,
    )

    if engine == "duckduckgo":
        results = _duckduckgo_html_results(query, num_results)
        source = "duckduckgo_html"
    else:
        results = _google_serp_results(query, num_results, headless=headless)
        source = "google_selenium"
        if not results:
            logger.info("[web_search] Google SERP empty; trying DuckDuckGo HTML fallback query=%r", query)
            results = _duckduckgo_html_results(query, num_results)
            source = "duckduckgo_html_fallback"

    if not results:
        logger.error(
            "[web_search] no SERP results query=%r source=%s (check connectivity or try WEB_RESEARCH_ENGINE=duckduckgo)",
            query,
            source,
        )
        return {
            "success": False,
            "results": [],
            "error": "No search results found (try WEB_RESEARCH_ENGINE=duckduckgo or check connectivity).",
            "source": source,
        }

    for i, r in enumerate(results, 1):
        logger.info(
            "[web_search] SERP hit %d/%d title=%r url=%s",
            i,
            len(results),
            (r.get("title") or "")[:100],
            r.get("url", ""),
        )
    logger.info("[web_search] SERP complete query=%r source=%s total=%d", query, source, len(results))

    return {"success": True, "results": results, "error": None, "source": source}
