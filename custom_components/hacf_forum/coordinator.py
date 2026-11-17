"""Lecture périodique du forum : derniers sujets, sujets du membre, notifications."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import re
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ForumAuthError, ForumClient, ForumError
from .const import (
    BASE_URL,
    CONF_BOOKMARKS,
    CONF_CONTRIBUTORS,
    CONF_FORUM_STATS,
    CONF_HIDE_SOLVED,
    CONF_MESSAGES,
    CONF_POPULAR,
    CONF_POPULAR_PERIOD,
    CONF_POSTS,
    CONF_PROFILE,
    CONF_SEARCH,
    CONF_TRACKED,
    CONF_UNANSWERED,
    CONF_UNREAD,
    DEFAULT_POPULAR_PERIOD,
    PERIODS,
    SLOW_HOURS,
    CONF_CATEGORY,
    CONF_TAG,
    CONF_NEWS,
    CONF_SCAN_MINUTES,
    CONF_TOPICS,
    CONF_USERNAME,
    DEFAULT_SCAN_MINUTES,
    DEFAULT_NEWS,
    DEFAULT_TOPICS,
    DOMAIN,
    MIN_SCAN_MINUTES,
    NEWS_HOURS,
    NEWS_ITEMS,
)
from .news import parse_feed

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


def _unread_posts(t: dict[str, Any]) -> int:
    """Messages non lus d'un sujet, pour le membre relié (0 sans compte)."""
    for key in ("unread_posts", "unread", "new_posts"):
        if isinstance(t.get(key), int) and t[key] > 0:
            return int(t[key]) + (int(t.get("new_posts") or 0) if key != "new_posts" else 0)
    last_read = t.get("last_read_post_number")
    if isinstance(last_read, int):
        return max(0, int(t.get("highest_post_number") or 0) - last_read)
    return int(t.get("posts_count") or 0) if t.get("unseen") else 0


def topic_url(topic: dict[str, Any], post_number: int | None = None) -> str:
    url = f"{BASE_URL}/t/{topic.get('slug') or 'sujet'}/{topic.get('id')}"
    return f"{url}/{post_number}" if post_number else url



def _plain(html: str | None, size: int = 180) -> str:
    """Texte d'un message HTML (cooked), sans balises, raccourci."""
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    return text if len(text) <= size else text[: size - 1].rstrip() + "…"


def normalize_tag(value: Any) -> str | None:
    """Étiquette saisie (« IA », « #ia ») ramenée à la forme du forum (« ia ») ; vide = aucune."""
    tag = str(value or "").strip().lstrip("#").strip().lower().replace(" ", "-")
    return tag or None

class ForumCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Un appel par liste à chaque mise à jour, catégories en cache."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: ForumClient) -> None:
        minutes = max(MIN_SCAN_MINUTES, int(entry.options.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES)))
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=timedelta(minutes=minutes))
        self.client = client
        self._categories: dict[int, dict[str, Any]] = {}
        self._categories_at = 0.0
        self._news: list[dict[str, Any]] = []
        self._news_at = 0.0
        self._news_etag: str | None = None
        self._news_modified: str | None = None
        self.news_error: str | None = None
        # fonctions relues une fois par heure : (heure de lecture, données)
        self._slow: dict[str, tuple[float, Any]] = {}
        # dernière valeur lue de chaque fonction facultative, gardée si le forum ne répond pas
        self._extra: dict[str, Any] = {}

    def option(self, key: str) -> bool:
        """Interrupteur d'une fonction facultative (désactivée par défaut)."""
        return bool(self.config_entry.options.get(key, False))

    @property
    def search_query(self) -> str | None:
        return str(self.config_entry.options.get(CONF_SEARCH) or "").strip() or None

    @property
    def username(self) -> str | None:
        return (self.config_entry.data.get(CONF_USERNAME) or "").strip() or None

    @property
    def has_account(self) -> bool:
        return self.client.has_key

    @property
    def news_enabled(self) -> bool:
        return bool(self.config_entry.options.get(CONF_NEWS, DEFAULT_NEWS))

    async def news(self) -> list[dict[str, Any]]:
        """Actualités de hacf.fr, relues toutes les 3 heures ; en cas d'échec, la liste précédente est gardée."""
        if self._news_at and time.monotonic() - self._news_at < NEWS_HOURS * 3600:
            return self._news
        self._news_at = time.monotonic()
        try:
            body, self._news_etag, self._news_modified = await self.client.news_feed(self._news_etag, self._news_modified)
            if body is not None:
                self._news = await self.hass.async_add_executor_job(parse_feed, body, NEWS_ITEMS)
            self.news_error = None
        except (ForumError, ValueError) as err:
            if self.news_error is None:
                _LOGGER.warning("Actualités de hacf.fr illisibles (nouvel essai dans 30 minutes) : %s", err)
            self.news_error = str(err)
            # nouvel essai dans 30 minutes
            self._news_at = time.monotonic() - NEWS_HOURS * 3600 + 1800
        return self._news

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
                "slug": c.get("slug") or str(cid),
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
                "unread": _unread_posts(t),
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
        tag = normalize_tag(self.config_entry.options.get(CONF_TAG))
        cats = await self.categories()
        result: dict[str, Any] = {"updated": datetime.now(UTC).isoformat()}
        try:
            cat = cats.get(int(category)) if category else None
            latest = await self.client.latest(int(category) if category else None, tag, (cat or {}).get("slug"))
            every = self._topics(latest, cats, 100)
            if self.option(CONF_HIDE_SOLVED):
                every = [t for t in every if not t["solved"]]
            result["latest"] = every[:limit]
            if self.option(CONF_UNANSWERED):
                # sans réponse : tirés de la même liste, aucune requête de plus
                result["unanswered"] = [t for t in every if not t["replies"] and not t["pinned"] and not t["closed"]][:limit]
            result["category"] = cat
            result["tag"] = tag
            if self.username:
                result["mine"] = self._topics(await self.client.created_by(self.username), cats, limit)
        except ForumError as err:
            raise UpdateFailed(f"Forum HACF injoignable : {err}") from err
        if self.news_enabled:
            result["news"] = await self.news()
        await self._public_extras(result, cats, limit)
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
            await self._account_extras(result, cats, limit, me.get("username") or self.username)
        return result

    async def _keep(self, key: str, result: dict[str, Any], fetch: Any) -> None:
        """Fonction facultative : nouvelle valeur, ou la précédente si le forum ne répond pas."""
        try:
            self._extra[key] = await fetch()
        except ForumAuthError:
            raise
        except (ForumError, KeyError, TypeError, ValueError) as err:
            _LOGGER.debug("%s illisible : %s", key, err)
        if key in self._extra:
            result[key] = self._extra[key]

    async def _hourly(self, key: str, fetch: Any) -> Any:
        """Lecture au plus une fois par heure (profil, statistiques, contributeurs)."""
        cached = self._slow.get(key)
        if cached and time.monotonic() - cached[0] < SLOW_HOURS * 3600:
            return cached[1]
        data = await fetch()
        self._slow[key] = (time.monotonic(), data)
        return data

    async def _public_extras(self, result: dict[str, Any], cats: dict[int, dict[str, Any]], limit: int) -> None:
        if self.option(CONF_POPULAR):
            period = self.config_entry.options.get(CONF_POPULAR_PERIOD) or DEFAULT_POPULAR_PERIOD
            period = period if period in PERIODS else DEFAULT_POPULAR_PERIOD

            async def popular() -> list[dict[str, Any]]:
                return self._topics(await self.client.top(period), cats, limit)

            await self._keep("popular", result, popular)
            result["popular_period"] = period
        if query := self.search_query:

            async def search() -> list[dict[str, Any]]:
                return self._search(await self.client.search(query), cats, limit)

            await self._keep("search", result, search)
            result["search_query"] = query
        if self.option(CONF_POSTS):

            async def posts() -> list[dict[str, Any]]:
                return self._posts(await self.client.posts(), cats, limit)

            await self._keep("posts", result, posts)
        if self.option(CONF_PROFILE) and self.username:
            username = self.username

            async def profile() -> dict[str, Any]:
                return await self._hourly("profile", lambda: self._profile(username))

            await self._keep("profile", result, profile)
        if self.option(CONF_FORUM_STATS):

            async def stats() -> dict[str, Any]:
                about = await self._hourly("about", self.client.about)
                return dict((about.get("about") or {}).get("stats") or {})

            await self._keep("forum_stats", result, stats)
        if self.option(CONF_CONTRIBUTORS):

            async def contributors() -> list[dict[str, Any]]:
                return self._contributors(await self._hourly("directory", lambda: self.client.directory("weekly")))

            await self._keep("contributors", result, contributors)

    async def _account_extras(self, result: dict[str, Any], cats: dict[int, dict[str, Any]], limit: int, account: str | None) -> None:
        try:
            if self.option(CONF_UNREAD):

                async def unread() -> list[dict[str, Any]]:
                    return self._topics(await self.client.unread(), cats, limit)

                async def new() -> list[dict[str, Any]]:
                    return self._topics(await self.client.new_topics(), cats, limit)

                await self._keep("unread_topics", result, unread)
                await self._keep("new_topics", result, new)
            if self.option(CONF_TRACKED):

                async def tracked() -> list[dict[str, Any]]:
                    return self._topics(await self.client.tracked(), cats, limit)

                await self._keep("tracked", result, tracked)
            if self.option(CONF_BOOKMARKS) and account:

                async def bookmarks() -> list[dict[str, Any]]:
                    return self._bookmarks(await self.client.bookmarks(account), limit)

                await self._keep("bookmarks", result, bookmarks)
            if self.option(CONF_MESSAGES) and account:

                async def messages() -> list[dict[str, Any]]:
                    return self._topics(await self.client.private_messages(account), cats, limit)

                await self._keep("messages", result, messages)
        except ForumAuthError as err:
            raise ConfigEntryAuthFailed("La clé du compte HACF a été refusée") from err

    def _search(self, data: dict[str, Any], cats: dict[int, dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        """Résultats de recherche : un sujet par ligne, avec l'auteur et la date du message trouvé."""
        found = {}
        for p in data.get("posts") or []:
            if isinstance(p, dict) and p.get("topic_id") not in found:
                found[p.get("topic_id")] = p
        topics, post_urls = [], {}
        for t in data.get("topics") or []:
            if not isinstance(t, dict):
                continue
            p = found.get(t.get("id")) or {}
            topics.append({**t, "last_poster_username": t.get("last_poster_username") or p.get("username"),
                           "last_posted_at": t.get("last_posted_at") or p.get("created_at")})
            if p.get("post_number"):
                post_urls[t.get("id")] = topic_url(t, p.get("post_number"))
        users = [{"username": p.get("username"), "avatar_template": p.get("avatar_template")}
                 for p in found.values() if p.get("username")]
        out = self._topics({"topic_list": {"topics": topics}, "users": users}, cats, limit)
        for t in out:
            p = found.get(t["id"]) or {}
            t["excerpt"] = _plain(p.get("blurb"))
            t["url"] = post_urls.get(t["id"], t["url"])
        return out

    def _posts(self, data: dict[str, Any], cats: dict[int, dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        """Derniers messages : sujet, auteur, extrait et lien vers le message."""
        out = []
        for p in data.get("latest_posts") or []:
            if not isinstance(p, dict) or p.get("hidden") or p.get("deleted_at"):
                continue
            cat = cats.get(p.get("category_id")) or {}
            topic = {"id": p.get("topic_id"), "slug": p.get("topic_slug")}
            out.append({
                "id": p.get("id"),
                "title": p.get("topic_title") or p.get("topic_html_title") or "",
                "url": topic_url(topic, p.get("post_number")),
                "excerpt": _plain(p.get("cooked") or p.get("excerpt")),
                "user": p.get("username") or "",
                "avatar": _avatar(p.get("avatar_template")),
                "created_at": p.get("created_at"),
                "category": cat.get("full_name"),
                "category_color": cat.get("color"),
            })
            if len(out) >= limit:
                break
        return out

    def _bookmarks(self, data: dict[str, Any], limit: int) -> list[dict[str, Any]]:
        """Signets : titre, lien, nom donné et rappel éventuel."""
        raw = (data.get("user_bookmark_list") or {}).get("bookmarks") or data.get("bookmarks") or []
        out = []
        for b in raw:
            if not isinstance(b, dict):
                continue
            url = b.get("bookmarkable_url") or ""
            if url.startswith("/"):
                url = f"{BASE_URL}{url}"
            elif not url.startswith(BASE_URL):
                url = topic_url({"id": b.get("topic_id"), "slug": b.get("slug")}, b.get("linked_post_number"))
            out.append({
                "id": b.get("id"),
                "title": b.get("title") or b.get("fancy_title") or "",
                "name": b.get("name") or "",
                "url": url,
                "excerpt": _plain(b.get("excerpt")),
                "created_at": b.get("created_at"),
                "reminder_at": b.get("reminder_at"),
            })
            if len(out) >= limit:
                break
        return out

    async def _profile(self, username: str) -> dict[str, Any]:
        """Résumé, niveau de confiance et badges du membre (3 requêtes, une fois par heure)."""
        summary = (await self.client.user_summary(username)).get("user_summary") or {}
        user = (await self.client.user(username)).get("user") or {}
        raw = await self.client.user_badges(username)
        names = {b.get("id"): b for b in raw.get("badges") or [] if isinstance(b, dict)}
        badges = []
        for ub in raw.get("user_badges") or []:
            b = names.get(ub.get("badge_id")) or {}
            if b:
                badges.append({"name": b.get("name") or "", "granted_at": ub.get("granted_at"),
                               "url": f"{BASE_URL}/badges/{b.get('id')}/{b.get('slug') or ''}"})
        badges.sort(key=lambda b: b.get("granted_at") or "", reverse=True)
        return {
            "likes_received": summary.get("likes_received"),
            "likes_given": summary.get("likes_given"),
            "posts": summary.get("post_count"),
            "topics": summary.get("topic_count"),
            "days_visited": summary.get("days_visited"),
            "solutions": summary.get("solved_count"),
            "trust_level": user.get("trust_level"),
            "badges": badges,
        }

    def _contributors(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Dix membres les plus aimés de la semaine."""
        out = []
        for item in data.get("directory_items") or []:
            u = (item or {}).get("user") or {}
            if not u.get("username"):
                continue
            out.append({
                "username": u.get("username"),
                "avatar": _avatar(u.get("avatar_template")),
                "likes_received": item.get("likes_received") or 0,
                "posts": item.get("post_count") or 0,
                "solutions": item.get("solutions") or 0,
                "url": f"{BASE_URL}/u/{u.get('username')}",
            })
            if len(out) >= 10:
                break
        return out
