"""Lecture périodique du forum : derniers sujets, sujets du membre, notifications."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ForumAuthError, ForumClient, ForumError
from .const import (
    BASE_URL,
    CONF_CATEGORY,
    CONF_SCAN_MINUTES,
    CONF_TOPICS,
    CONF_USERNAME,
    DEFAULT_SCAN_MINUTES,
    DEFAULT_TOPICS,
    DOMAIN,
    MIN_SCAN_MINUTES,
)

_LOGGER = logging.getLogger(__name__)

# Catégories relues une fois par jour (noms et couleurs changent rarement)
CATEGORIES_TTL = 24 * 3600

# Type de notification Discourse → clé utilisée par la carte (libellé et icône)
NOTIFICATION_TYPES = {
    1: "mentioned", 2: "replied", 3: "quoted", 4: "edited", 5: "liked", 6: "private_message",
    7: "invited_to_private_message", 8: "invitee_accepted", 9: "posted", 10: "moved_post", 11: "linked",
    12: "granted_badge", 13: "invited_to_topic", 15: "group_mentioned", 16: "group_message_summary",
    17: "watching_first_post", 18: "topic_reminder", 19: "liked_consolidated", 20: "post_approved",
    24: "bookmark_reminder", 25: "reaction", 37: "watching_category_or_tag",
}


def _avatar(template: str | None, size: int = 48) -> str | None:
    if not template:
        return None
    url = template.replace("{size}", str(size))
    return url if url.startswith("http") else f"{BASE_URL}{url}"


def topic_url(topic: dict[str, Any], post_number: int | None = None) -> str:
    url = f"{BASE_URL}/t/{topic.get('slug') or 'sujet'}/{topic.get('id')}"
    return f"{url}/{post_number}" if post_number else url


class ForumCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Un appel par liste à chaque mise à jour, catégories en cache."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: ForumClient) -> None:
        minutes = max(MIN_SCAN_MINUTES, int(entry.options.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES)))
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=timedelta(minutes=minutes))
        self.client = client
        self._categories: dict[int, dict[str, Any]] = {}
        self._categories_at = 0.0

    @property
    def username(self) -> str | None:
        return (self.config_entry.data.get(CONF_USERNAME) or "").strip() or None

    @property
    def has_account(self) -> bool:
        return self.client.has_key

    async def categories(self) -> dict[int, dict[str, Any]]:
        """Catégories par identifiant : nom (avec le parent), couleur, lien."""
        if self._categories and time.monotonic() - self._categories_at < CATEGORIES_TTL:
            return self._categories
        try:
            site = await self.client.site()
        except ForumError as err:
            _LOGGER.debug("Catégories du forum illisibles : %s", err)
            return self._categories
        raw = {c["id"]: c for c in site.get("categories", []) if isinstance(c, dict) and "id" in c}
        cats = {}
        for cid, c in raw.items():
            parent = raw.get(c.get("parent_category_id"))
            name = c.get("name") or str(cid)
            cats[cid] = {
                "id": cid,
                "name": name,
                "full_name": f"{parent.get('name')} › {name}" if parent else name,
                "color": f"#{c.get('color') or '8fa0b8'}",
                "url": f"{BASE_URL}/c/{c.get('slug') or cid}/{cid}",
            }
        self._categories, self._categories_at = cats, time.monotonic()
        return cats

    def _topics(self, data: dict[str, Any], cats: dict[int, dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        users = {u.get("username"): u for u in data.get("users", []) if isinstance(u, dict)}
        out = []
        for t in (data.get("topic_list") or {}).get("topics", []):
            if not isinstance(t, dict) or t.get("visible") is False:
                continue
            cat = cats.get(t.get("category_id")) or {}
            last = t.get("last_poster_username")
            out.append({
                "id": t.get("id"),
                "title": t.get("title") or t.get("fancy_title") or "",
                "url": topic_url(t),
                "last_url": topic_url(t, t.get("highest_post_number")),
                "category": cat.get("full_name"),
                "category_color": cat.get("color"),
                "posts": t.get("posts_count") or 0,
                "replies": t.get("reply_count") or max(0, (t.get("posts_count") or 1) - 1),
                "highest_post": t.get("highest_post_number") or t.get("posts_count") or 0,
                "views": t.get("views") or 0,
                "likes": t.get("like_count") or 0,
                "created_at": t.get("created_at"),
                "last_posted_at": t.get("last_posted_at") or t.get("bumped_at"),
                "last_poster": last,
                "last_poster_avatar": _avatar((users.get(last) or {}).get("avatar_template")),
                "pinned": bool(t.get("pinned")),
                "closed": bool(t.get("closed")),
                "solved": bool(t.get("has_accepted_answer")),
                "tags": [x if isinstance(x, str) else x.get("name") for x in t.get("tags") or []],
            })
            if len(out) >= limit:
                break
        return out

    def _notifications(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        out = []
        for n in data.get("notifications", [])[:30]:
            if not isinstance(n, dict):
                continue
            d = n.get("data") or {}
            topic = {"id": n.get("topic_id"), "slug": n.get("slug")}
            kind = NOTIFICATION_TYPES.get(n.get("notification_type"), "other")
            if n.get("topic_id"):
                url = topic_url(topic, n.get("post_number"))
            elif kind == "granted_badge" and d.get("badge_id"):
                url = f"{BASE_URL}/badges/{d.get('badge_id')}/{d.get('badge_slug') or ''}"
            else:
                url = f"{BASE_URL}/my/notifications"
            out.append({
                "id": n.get("id"),
                "type": kind,
                "read": bool(n.get("read")),
                "high_priority": bool(n.get("high_priority")),
                "created_at": n.get("created_at"),
                "title": d.get("topic_title") or n.get("fancy_title") or d.get("badge_name") or "",
                "user": d.get("display_username") or d.get("original_username") or d.get("username") or "",
                "badge": d.get("badge_name"),
                "count": d.get("count"),
                "url": url,
            })
        return out

    async def _async_update_data(self) -> dict[str, Any]:
        limit = int(self.config_entry.options.get(CONF_TOPICS, DEFAULT_TOPICS))
        category = self.config_entry.options.get(CONF_CATEGORY) or None
        cats = await self.categories()
        result: dict[str, Any] = {"updated": datetime.now(UTC).isoformat()}
        try:
            latest = await self.client.latest(int(category) if category else None)
            result["latest"] = self._topics(latest, cats, limit)
            result["category"] = cats.get(int(category)) if category else None
            if self.username:
                result["mine"] = self._topics(await self.client.created_by(self.username), cats, limit)
        except ForumError as err:
            raise UpdateFailed(f"Forum HACF injoignable : {err}") from err
        if self.has_account:
            try:
                me = await self.client.current_user()
                notes = await self.client.notifications()
            except ForumAuthError as err:
                raise ConfigEntryAuthFailed("La clé du compte HACF a été refusée") from err
            except ForumError as err:
                raise UpdateFailed(f"Notifications illisibles : {err}") from err
            items = self._notifications(notes)
            result["notifications"] = items
            if me.get("all_unread_notifications_count") is not None:
                result["unread"] = int(me["all_unread_notifications_count"])
            elif me.get("unread_notifications") is not None:
                result["unread"] = int(me.get("unread_notifications") or 0) + int(me.get("unread_high_priority_notifications") or 0)
            else:
                result["unread"] = sum(1 for n in items if not n["read"])
            result["account"] = me.get("username")
        return result
