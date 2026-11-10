"""Actualités du site hacf.fr : flux RSS public de la rubrique « Actualités » (site Ghost)."""
from __future__ import annotations

from email.utils import parsedate_to_datetime
import html
import re
from typing import Any
import xml.etree.ElementTree as ET

NEWS_SITE = "https://www.hacf.fr"
NEWS_PAGE = f"{NEWS_SITE}/tag/news/"
NEWS_FEED = f"{NEWS_SITE}/tag/news/rss/"

_NS = {"dc": "http://purl.org/dc/elements/1.1/", "media": "http://search.yahoo.com/mrss/"}
_TAGS = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"\s+")
SUMMARY_MAX = 220


def _site_url(url: str | None) -> str | None:
    """Liens et images : seulement vers le site hacf.fr."""
    url = (url or "").strip()
    return url if url.startswith(NEWS_SITE + "/") else None


def _text(value: str | None) -> str:
    text = _SPACES.sub(" ", html.unescape(_TAGS.sub(" ", value or ""))).strip()
    if len(text) > SUMMARY_MAX:
        text = text[:SUMMARY_MAX].rsplit(" ", 1)[0].rstrip(" ,;:.") + "…"
    return text


def parse_feed(xml: bytes, limit: int) -> list[dict[str, Any]]:
    """Articles du flux, du plus récent au plus ancien. ValueError si le flux est illisible."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as err:
        raise ValueError(f"flux illisible : {err}") from err
    out: list[dict[str, Any]] = []
    for item in root.iterfind("./channel/item"):
        url = _site_url(item.findtext("link"))
        title = _text(item.findtext("title"))
        if not url or not title:
            continue
        published = None
        if date := item.findtext("pubDate"):
            try:
                published = parsedate_to_datetime(date).isoformat()
            except (TypeError, ValueError):
                published = None
        media = item.find("media:content", _NS)
        out.append({
            "id": (item.findtext("guid") or url).strip(),
            "title": title,
            "url": url,
            "published_at": published,
            "author": _text(item.findtext("dc:creator", namespaces=_NS)) or None,
            "summary": _text(item.findtext("description")),
            "image": _site_url(media.get("url")) if media is not None else None,
        })
        if len(out) >= limit:
            break
    return out
