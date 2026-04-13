"""Load allowlisted feeds and parse RSS/Atom XML into plain entries."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
import yaml


@dataclass(frozen=True)
class RssEntry:
    """One item from a syndication feed."""

    title: str
    link: str
    summary: str
    published: str | None
    source_feed: str


def load_feed_config(path: str | Path) -> list[dict[str, Any]]:
    """Return enabled feed records from YAML (see config/feeds.yaml)."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    feeds = raw.get("feeds", []) if isinstance(raw, dict) else []
    out: list[dict[str, Any]] = []
    for row in feeds:
        if not isinstance(row, dict):
            continue
        if row.get("enabled", True) is False:
            continue
        url = row.get("url")
        if not url:
            continue
        out.append(row)
    return out


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def parse_rss_bytes(xml_bytes: bytes, source_feed_url: str) -> list[RssEntry]:
    """Parse RSS 2.0 or Atom-ish XML into RssEntry rows (best-effort, PoC scope)."""
    root = ET.fromstring(xml_bytes)
    tag = _strip_ns(root.tag).lower()
    entries: list[RssEntry] = []

    if tag == "rss":
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            if desc_el is None:
                desc_el = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
            pub_el = item.find("pubDate")
            if pub_el is None:
                pub_el = item.find("published")
            title = (title_el.text or "").strip() if title_el is not None and title_el.text else ""
            link = (link_el.text or "").strip() if link_el is not None and link_el.text else ""
            if not link:
                guid_el = item.find("guid")
                if guid_el is not None and guid_el.text:
                    link = guid_el.text.strip()
            summary = (desc_el.text or "").strip() if desc_el is not None and desc_el.text else ""
            published = (pub_el.text or "").strip() if pub_el is not None and pub_el.text else None
            if title or link:
                entries.append(
                    RssEntry(
                        title=title,
                        link=link,
                        summary=summary[:8000],
                        published=published,
                        source_feed=source_feed_url,
                    )
                )
        return entries

    if tag == "feed":  # Atom
        for item in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title_el = item.find("{http://www.w3.org/2005/Atom}title")
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            summary_el = item.find("{http://www.w3.org/2005/Atom}summary")
            content_el = item.find("{http://www.w3.org/2005/Atom}content")
            updated_el = item.find("{http://www.w3.org/2005/Atom}updated")
            published_el = item.find("{http://www.w3.org/2005/Atom}published")
            title = (title_el.text or "").strip() if title_el is not None and title_el.text else ""
            link = ""
            if link_el is not None:
                link = (link_el.get("href") or "").strip() or (link_el.text or "").strip()
            if not link:
                id_el = item.find("{http://www.w3.org/2005/Atom}id")
                if id_el is not None and id_el.text:
                    link = id_el.text.strip()
            summary = ""
            if content_el is not None and content_el.text:
                summary = content_el.text.strip()
            elif summary_el is not None and summary_el.text:
                summary = summary_el.text.strip()
            published = None
            if published_el is not None and published_el.text:
                published = published_el.text.strip()
            elif updated_el is not None and updated_el.text:
                published = updated_el.text.strip()
            if title or link:
                abs_link = urljoin(source_feed_url, link) if link and not link.startswith("http") else link
                entries.append(
                    RssEntry(
                        title=title,
                        link=abs_link,
                        summary=summary[:8000],
                        published=published,
                        source_feed=source_feed_url,
                    )
                )
        return entries

    return entries


def fetch_feed_entries(
    feed_url: str,
    *,
    timeout: float = 30.0,
    headers: dict[str, str] | None = None,
) -> list[RssEntry]:
    """HTTP GET feed_url and parse entries (live network; use parse_rss_bytes for fixtures)."""
    default_headers = {
        "User-Agent": "EventDrivenTradingSignalAgent/0.1 (+https://github.com/)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }
    merged = {**default_headers, **(headers or {})}
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(feed_url, headers=merged)
        response.raise_for_status()
        return parse_rss_bytes(response.content, feed_url)
