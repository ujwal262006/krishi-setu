"""
Krishi Setu — Crawler Service
Multi-format ingestion pipeline: HTML, PDF, CSV, JSON, XLSX, DOCX, XML
Async job pattern — crawl requests are queued, not blocking.
URL deduplication via SHA-256 hash.
Domain-scoped crawling with configurable rate limits per source.
"""

import hashlib
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Optional
from urllib.robotparser import RobotFileParser

import httpx
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.models import CrawlJob, CrawlJobStatus, Scheme, Source

settings = get_settings()


# ─── Utilities ────────────────────────────────────────────────────────────────

def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_url(url: str, base_url: str) -> Optional[str]:
    """Resolve relative URLs against the base URL."""
    try:
        resolved = urllib.parse.urljoin(base_url, url)
        parsed = urllib.parse.urlparse(resolved)
        # Only keep http/https
        if parsed.scheme not in ("http", "https"):
            return None
        return resolved
    except Exception:
        return None


def is_same_domain(url: str, base_url: str) -> bool:
    """Ensure we only crawl within the source's domain."""
    try:
        base_domain = urllib.parse.urlparse(base_url).netloc
        url_domain = urllib.parse.urlparse(url).netloc
        return url_domain == base_domain or url_domain.endswith(f".{base_domain}")
    except Exception:
        return False


def can_fetch(url: str, user_agent: str = "*") -> bool:
    """Check robots.txt — respect crawl rules."""
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # If robots.txt is unavailable, allow crawling
        return True


def fetch_url(
    url: str,
    timeout: int = 30,
    headers: Optional[dict] = None,
) -> Optional[requests.Response]:
    """Fetch a URL with error handling and timeout."""
    default_headers = {
        "User-Agent": (
            "KrishiSetuBot/1.0 (+https://krishisetu.gov.in/bot) "
            "Mozilla/5.0 (compatible)"
        ),
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
    }
    if headers:
        default_headers.update(headers)

    try:
        response = requests.get(
            url,
            headers=default_headers,
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        print(f"  [timeout] {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  [http error] {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [request error] {url}: {e}")
        return None


# ─── HTML Extractor ───────────────────────────────────────────────────────────

def extract_links(html: str, base_url: str) -> list[str]:
    """Extract all valid, same-domain links from an HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        normalized = normalize_url(href, base_url)
        if normalized and is_same_domain(normalized, base_url):
            # Skip non-content URLs
            skip_extensions = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".css", ".js")
            if not any(normalized.lower().endswith(ext) for ext in skip_extensions):
                links.append(normalized)
    return list(set(links))


def extract_scheme_data_from_html(
    html: str,
    url: str,
    source: Source,
) -> Optional[dict]:
    """
    Extract scheme data from an HTML page.
    Returns a dict if scheme data is detected, None otherwise.
    Filters out navigation, footer, form, and utility pages.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove boilerplate elements before any analysis
    for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # ── Negative filter — skip known non-scheme page patterns ──────────────────
    # Check URL patterns first (fast rejection)
    url_lower = url.lower()
    skip_url_patterns = [
        "/privacy", "/disclaimer", "/terms", "/contact", "/grievance",
        "/feedback", "/sitemap", "/login", "/register", "/signup",
        "/search", "/404", "/error", "/faq", "/help", "/about",
        "/social", "/media", "/video", "/gallery", "/download",
        "/screen-reader", "/accessibility", "/archive",
    ]
    if any(pattern in url_lower for pattern in skip_url_patterns):
        return None

    # ── Skip pages with very little meaningful content ─────────────────────────
    words = text.split()
    if len(words) < 100:
        return None

    # ── Negative keyword filter — skip utility/navigation pages ────────────────
    title_el = soup.find("title") or soup.find("h1")
    title_text = title_el.get_text(strip=True).lower() if title_el else ""

    skip_title_patterns = [
        "privacy policy", "disclaimer", "terms and condition",
        "contact us", "grievance", "feedback", "sitemap",
        "screen reader", "social media", "videos", "back",
        "registration form", "login", "sign in", "404",
        "beneficiary status", "voluntary surrender",
    ]
    if any(pattern in title_text for pattern in skip_title_patterns):
        return None

    # ── Positive filter — must have meaningful scheme content ──────────────────
    scheme_keywords = [
        "eligibility", "benefit", "scheme", "yojana", "subsidy",
        "farmer", "kisan", "apply", "criteria", "assistance",
        "grant", "loan", "pension", "insurance", "support",
    ]
    keyword_count = sum(1 for kw in scheme_keywords if kw.lower() in text.lower())
    if keyword_count < 3:
        return None

    # ── Extract best available title ───────────────────────────────────────────
    title = None
    for tag_name in ["h1", "h2", "title"]:
        el = soup.find(tag_name)
        if el:
            candidate = el.get_text(strip=True)
            if candidate and len(candidate) > 5:
                title = candidate[:500]
                break

    if not title or len(title) < 10:
        return None

    # Content hash for change detection
    content_hash = sha256_hash(text[:5000])
    url_hash = sha256_hash(url)

    return {
        "name": title,
        "description": text[:2000],
        "source_url": url,
        "url_hash": url_hash,
        "content_hash": content_hash,
        "ministry_id": source.ministry_id,
        "search_synonyms": [],
        "eligibility_criteria": {},
        "benefits": {},
    }

# ─── Core Crawl Function ──────────────────────────────────────────────────────

def crawl_source(
    source: Source,
    job: CrawlJob,
    db: Session,
    max_depth: Optional[int] = None,
) -> None:
    """
    BFS crawl of a source URL up to max_depth.
    Updates the CrawlJob record with progress.
    Respects rate limits configured per source.
    """
    max_depth = max_depth or source.max_depth
    rate_limit_delay = 1.0 / source.rate_limit_rps  # seconds between requests

    visited_urls: set[str] = set()
    queue: list[tuple[str, int]] = [(source.base_url, 0)]  # (url, depth)

    job.status = CrawlJobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    print(f"\n[crawl] Starting: {source.base_url} (max_depth={max_depth})")

    while queue:
        url, depth = queue.pop(0)

        if url in visited_urls:
            continue
        if depth > max_depth:
            continue

        visited_urls.add(url)
        job.urls_discovered = len(visited_urls)

        # Robots.txt check
        if source.respect_robots_txt and not can_fetch(url):
            print(f"  [robots] Blocked: {url}")
            continue

        # Rate limiting
        time.sleep(rate_limit_delay)

        # Fetch page
        response = fetch_url(url, timeout=settings.REQUEST_TIMEOUT_SECONDS)
        if not response:
            job.errors_count += 1
            db.commit()
            continue

        job.urls_crawled += 1

        content_type = response.headers.get("content-type", "").lower()

        if "text/html" in content_type:
            html = response.text

            # Extract and queue links for next depth
            if depth < max_depth:
                links = extract_links(html, source.base_url)
                for link in links:
                    if link not in visited_urls:
                        queue.append((link, depth + 1))

            # Try to extract scheme data
            scheme_data = extract_scheme_data_from_html(html, url, source)
            if scheme_data:
                _upsert_scheme(scheme_data, db)
                job.schemes_upserted += 1

        elif "application/pdf" in content_type:
            # PDF handling — delegate to extractor
            from app.services.extractor import extract_from_pdf_bytes
            scheme_data = extract_from_pdf_bytes(response.content, url, source)
            if scheme_data:
                _upsert_scheme(scheme_data, db)
                job.schemes_upserted += 1

        # Commit progress every 10 URLs
        if job.urls_crawled % 10 == 0:
            db.commit()
            print(f"  [progress] crawled={job.urls_crawled} schemes={job.schemes_upserted}")

    # Mark job complete
    job.status = CrawlJobStatus.COMPLETED
    job.completed_at = datetime.now(timezone.utc)

    # Update source last crawled
    source.last_crawled_at = datetime.now(timezone.utc)

    db.commit()
    print(f"[crawl] Done: urls={job.urls_crawled} schemes={job.schemes_upserted} errors={job.errors_count}")


def _upsert_scheme(data: dict, db: Session) -> None:
    """
    Insert or update a scheme based on url_hash.
    If content_hash is the same, skip (no changes).
    """
    existing = db.query(Scheme).filter(
        Scheme.url_hash == data["url_hash"]
    ).first()

    if existing:
        # Skip if content hasn't changed
        if existing.content_hash == data.get("content_hash"):
            return
        # Update changed fields
        for key, value in data.items():
            if key not in ("id", "created_at") and value is not None:
                setattr(existing, key, value)
        existing.last_updated_at = datetime.now(timezone.utc)
    else:
        # Generate slug from name
        import re
        slug_base = re.sub(r"[^a-z0-9]+", "-", data["name"].lower())[:200].strip("-")
        slug = slug_base

        # Ensure slug uniqueness
        counter = 1
        while db.query(Scheme).filter(Scheme.slug == slug).first():
            slug = f"{slug_base}-{counter}"
            counter += 1

        scheme = Scheme(
            slug=slug,
            last_updated_at=datetime.now(timezone.utc),
            **{k: v for k, v in data.items() if k != "slug"},
        )
        db.add(scheme)

    db.flush()
