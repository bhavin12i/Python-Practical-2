import json
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.utils.validators import UnsafeUrlError, UrlValidationError, validate_public_url, validate_redirect_url

REDIRECT_STATUSES = {301, 302, 303, 307, 308}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LinkAnalysis/1.0)",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
    "Accept-Language": "en-US,en;q=0.8",
}


class WebsiteFetchError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ExtractedWebsite:
    requested_url: str
    final_url: str
    title: str = ""
    meta_description: str = ""
    headings: list = field(default_factory=list)
    text: str = ""
    external_links: list = field(default_factory=list)
    status_code: int = 200
    word_count: int = 0
    char_count: int = 0
    truncated: bool = False
    content_source: str = "page_text"

    def as_dict(self):
        return {
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "title": self.title,
            "meta_description": self.meta_description,
            "headings_count": len(self.headings),
            "external_links_observed": len(self.external_links),
            "status_code": self.status_code,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "truncated": self.truncated,
            "content_source": self.content_source,
        }

    def prompt_content(self, max_chars):
        lines = [
            "Requested URL: " + self.requested_url,
            "Final URL: " + self.final_url,
            "Page title: " + (self.title or "not found"),
            "Meta description: " + (self.meta_description or "not found"),
            "Headings: " + (" | ".join(self.headings) if self.headings else "not found"),
            "Observed external links: "
            + (" | ".join(self.external_links) if self.external_links else "none observed"),
            "Content source: " + self.content_source,
            "Page text: " + (self.text or "no readable text found"),
        ]
        content = "\n".join(lines)
        if len(content) > max_chars:
            return content[:max_chars].rsplit(" ", 1)[0] + " [truncated]"
        return content


def _clean(value):
    return " ".join(value.split()).strip()


def _collect_meta(soup):
    values = {}
    for tag in soup.find_all("meta"):
        key = _clean(str(tag.get("property") or tag.get("name") or tag.get("itemprop") or "")).lower()
        content = _clean(str(tag.get("content", "")))
        if key and content and key not in values:
            values[key] = content
    return values


def _first(meta, *keys):
    for key in keys:
        if meta.get(key):
            return meta[key]
    return ""


def _jsonld_nodes(soup, limit=8):
    nodes = []
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string or tag.get_text() or ""
        if not raw.strip() or len(raw) > 30000:
            continue
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            continue
        stack = [data]
        while stack and len(nodes) < limit:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                nodes.append(node)
                for key in ("@graph", "mainEntity", "itemListElement", "hasPart"):
                    child = node.get(key)
                    if isinstance(child, list):
                        stack.extend(child)
                    elif isinstance(child, dict):
                        stack.append(child)
    return nodes


def _metadata_lines(soup, meta):
    lines = []
    seen = []

    def add(label, value, limit=600):
        value = _clean(value or "")[:limit]
        if not value:
            return
        key = "".join(value.lower().split())
        if any(len(key) > 100 and len(old) > 100 and key[:100] == old[:100] for old in seen):
            return
        seen.append(key)
        lines.append((label, value))

    add("Site", _first(meta, "og:site_name", "application-title", "twitter:site"))
    add("Page type", _first(meta, "og:type"))
    add("Description", _first(meta, "og:description", "twitter:description"), 1200)
    add("Description", meta.get("description"), 1200)
    add("Keywords", _first(meta, "keywords", "news_keywords"))
    add("Author", _first(meta, "author", "article:author"))

    index = 1
    while meta.get("twitter:label" + str(index)) or meta.get("twitter:data" + str(index)):
        label = meta.get("twitter:label" + str(index), "")
        data = meta.get("twitter:data" + str(index), "")
        add("Profile detail", (label + " " + data).strip())
        index += 1

    for node in _jsonld_nodes(soup)[:5]:
        kind = _clean(str(node.get("@type", "")))
        name = _clean(str(node.get("name") or node.get("alternateName") or ""))
        description = _clean(str(node.get("description") or ""))
        if not (kind or name or description):
            continue
        label = "Structured data"
        if kind:
            label += " (" + kind + ")"
        if name:
            add(label, name)
        add(label + " description", description, 800)

    return lines


def _parse(html, final_url):
    soup = BeautifulSoup(html, "html.parser")
    meta = _collect_meta(soup)
    metadata_lines = _metadata_lines(soup, meta)

    title = _clean(str(meta.get("og:title") or meta.get("twitter:title") or ""))
    if not title:
        title = _clean(soup.title.get_text(" ", strip=True)) if soup.title else ""
    description = _first(meta, "og:description", "twitter:description", "description")

    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe", "template"]):
        tag.decompose()

    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        value = _clean(tag.get_text(" ", strip=True))
        if value and value not in headings:
            headings.append(value)

    seen = set()
    parts = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li", "td", "th", "a", "strong"]):
        value = _clean(tag.get_text(" ", strip=True))
        if len(value) < 3 or value in seen:
            continue
        seen.add(value)
        parts.append(value)

    body = _clean(" ".join(parts))
    if len(body.split()) < 5:
        for tag in soup(["head", "title"]):
            tag.decompose()
        body = _clean(soup.get_text(" ", strip=True))

    fresh_metadata = [
        (label, value)
        for label, value in metadata_lines
        if len(value) <= 40 or value.lower() not in body.lower()
    ]
    if fresh_metadata:
        metadata_text = "Metadata extracted from the page:\n" + "\n".join(
            label + ": " + value for label, value in fresh_metadata
        )
        if not body:
            text = metadata_text
            content_source = "page_metadata"
        else:
            text = body + "\n\n" + metadata_text
            content_source = "page_text+metadata"
    else:
        text = body
        content_source = "page_text" if body else "unavailable"

    host = urlsplit(final_url).netloc.lower()
    links = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href", "")).strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        absolute = urljoin(final_url, href)
        parsed = urlsplit(absolute)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            continue
        if parsed.netloc.lower() == host or absolute in links:
            continue
        links.append(absolute)
        if len(links) >= 20:
            break

    return ExtractedWebsite(
        requested_url=final_url,
        final_url=final_url,
        title=title,
        meta_description=description,
        headings=headings[:40],
        text=text,
        external_links=links,
        word_count=len(text.split()),
        char_count=len(text),
        content_source=content_source,
    )


async def extract_website(url, client=None):
    validated_url = await validate_public_url(url)
    owns_client = client is None
    client = client or httpx.AsyncClient(
        timeout=settings.website_timeout_seconds,
        follow_redirects=False,
        headers=BROWSER_HEADERS,
    )

    try:
        current_url = validated_url
        final_url = validated_url
        html = b""
        status_code = 200

        for hop in range(6):
            safe_url = await validate_redirect_url(current_url)
            try:
                async with client.stream("GET", safe_url, follow_redirects=False) as response:
                    status_code = response.status_code

                    if status_code in REDIRECT_STATUSES:
                        location = response.headers.get("location")
                        if not location:
                            raise WebsiteFetchError("Redirect had no location header", 502)
                        current_url = urljoin(safe_url, location)
                        if hop == 5:
                            raise WebsiteFetchError("Too many redirects while fetching website", 400)
                        continue

                    if status_code >= 400:
                        raise WebsiteFetchError("Website returned HTTP " + str(status_code), 502)

                    content_type = response.headers.get("content-type", "").lower()
                    if content_type and not any(t in content_type for t in ("text/html", "application/xhtml+xml")):
                        raise WebsiteFetchError("Unsupported content type: " + content_type, 415)

                    chunks = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        chunks.append(chunk)
                        total += len(chunk)
                        if total >= settings.website_max_bytes:
                            break
                    html = b"".join(chunks)[: settings.website_max_bytes]
                    final_url = str(response.url)
                    break
            except httpx.TimeoutException as exc:
                raise WebsiteFetchError("Website request timed out", 504) from exc
            except (httpx.ConnectError, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                raise WebsiteFetchError("Website could not be reached", 502) from exc
        else:
            raise WebsiteFetchError("Too many redirects while fetching website", 400)

        if not html.strip():
            raise WebsiteFetchError("Website returned an empty response", 502)

        result = _parse(html, final_url)
        result.requested_url = url
        result.status_code = status_code

        limit = settings.website_max_content_chars
        if len(result.text) > limit:
            result.text = result.text[:limit].rsplit(" ", 1)[0]
            result.truncated = True
        result.char_count = len(result.text)
        result.word_count = len(result.text.split())
        if result.content_source == "unavailable":
            raise WebsiteFetchError(
                "No readable content could be extracted from this page. "
                "The site may require JavaScript or block automated requests.",
                422,
            )
        return result
    except (UrlValidationError, UnsafeUrlError) as exc:
        if isinstance(exc, UnsafeUrlError):
            raise
        raise WebsiteFetchError(str(exc), 400) from exc
    finally:
        if owns_client:
            await client.aclose()
