"""Capteurs : derniers sujets, mes sujets, notifications non lues, et fonctions facultatives (listes en attributs pour la carte)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import ForumConfigEntry
from .const import (
    BASE_URL,
    CONF_CONTRIBUTORS,
    CONF_FORUM_STATS,
    CONF_POSTS,
    CONF_PROFILE,
    CONF_TRACKED,
    CONF_BOOKMARKS,
    CONF_MESSAGES,
    CONF_POPULAR,
    CONF_UNANSWERED,
    CONF_UNREAD,
    DOMAIN,
    VERSION,
)
from .coordinator import ForumCoordinator
from .news import NEWS_PAGE


async def async_setup_entry(hass: HomeAssistant, entry: ForumConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [LatestTopicsSensor(coordinator)]
    if coordinator.username:
        entities.append(MyTopicsSensor(coordinator))
    if coordinator.has_account:
        entities.append(NotificationsSensor(coordinator))
    if coordinator.news_enabled:
        entities.append(NewsSensor(coordinator))
    entities.extend(_optional_sensors(coordinator))
    async_add_entities(entities)


def _optional_sensors(c: ForumCoordinator) -> list[SensorEntity]:
    """Capteurs des fonctions facultatives, créés seulement si leur interrupteur est activé."""
    out: list[SensorEntity] = []
    if c.option(CONF_POPULAR):
        out.append(TopicListSensor(c, "popular_topics", "popular", "mdi:fire",
                                   lambda d: f"{BASE_URL}/top?period={d.get('popular_period') or 'weekly'}", ("popular_period",)))
    if c.option(CONF_UNANSWERED):
        out.append(TopicListSensor(c, "unanswered_topics", "unanswered", "mdi:help-circle-outline", lambda d: f"{BASE_URL}/latest"))
    if c.search_query:
        out.append(TopicListSensor(c, "search_results", "search", "mdi:magnify",
                                   lambda d: f"{BASE_URL}/search?q={quote(d.get('search_query') or '')}", ("search_query",)))
    if c.option(CONF_POSTS):
        out.append(TopicListSensor(c, "latest_posts", "posts", "mdi:message-reply-text-outline", lambda d: f"{BASE_URL}/posts", attr="posts"))
    if c.option(CONF_PROFILE) and c.username:
        for key, field, icon in (("likes_received", "likes_received", "mdi:heart"), ("likes_given", "likes_given", "mdi:heart-outline"),
                                 ("posts_count", "posts", "mdi:message-text"), ("topics_count", "topics", "mdi:forum"),
                                 ("days_visited", "days_visited", "mdi:calendar-check"), ("solutions", "solutions", "mdi:check-decagram"),
                                 ("trust_level", "trust_level", "mdi:shield-account")):
            out.append(ValueSensor(c, key, "profile", field, icon))
        out.append(BadgesSensor(c))
    if c.option(CONF_FORUM_STATS):
        for key, field, icon in (("forum_members", "users_count", "mdi:account-group"),
                                 ("forum_active_users", "active_users_7_days", "mdi:account-clock"),
                                 ("forum_topics", "topics_count", "mdi:forum-outline"), ("forum_posts", "posts_count", "mdi:message-text-outline")):
            out.append(ValueSensor(c, key, "forum_stats", field, icon))
    if c.option(CONF_CONTRIBUTORS):
        out.append(ContributorsSensor(c))
    if c.has_account:
        if c.option(CONF_UNREAD):
            out.append(TopicListSensor(c, "unread_topics", "unread_topics", "mdi:email-mark-as-unread", lambda d: f"{BASE_URL}/unread"))
            out.append(TopicListSensor(c, "new_topics", "new_topics", "mdi:new-box", lambda d: f"{BASE_URL}/new"))
        if c.option(CONF_TRACKED):
            out.append(TopicListSensor(c, "tracked_topics", "tracked", "mdi:eye-outline", lambda d: f"{BASE_URL}/latest?f=tracked"))
        if c.option(CONF_BOOKMARKS):
            out.append(TopicListSensor(c, "bookmarks", "bookmarks", "mdi:bookmark-outline",
                                       lambda d: f"{BASE_URL}/u/{d.get('account') or ''}/activity/bookmarks", attr="bookmarks"))
        if c.option(CONF_MESSAGES):
            out.append(MessagesSensor(c))
    return out


def device_info(coordinator: ForumCoordinator) -> DeviceInfo:
    """Appareil commun à toutes les entités de l'intégration."""
    entry = coordinator.config_entry
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="HACF (non officiel)",
        model="Forum Discourse",
        sw_version=VERSION,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=BASE_URL,
    )


class ForumEntity(CoordinatorEntity[ForumCoordinator], SensorEntity):
    _attr_has_entity_name = True
    # listes destinées à la carte : pas d'historique dans la base de Home Assistant
    _unrecorded_attributes = frozenset({"topics", "notifications", "category", "tag", "articles", "posts", "bookmarks",
                                        "badges", "contributors", "search_query", "popular_period"})

    def __init__(self, coordinator: ForumCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info(coordinator)


def _recent(topics: list[dict[str, Any]], hours: int = 24) -> int:
    since = datetime.now(UTC) - timedelta(hours=hours)
    n = 0
    for t in topics:
        when = dt_util.parse_datetime(t.get("last_posted_at") or "")
        if when and when >= since:
            n += 1
    return n


class LatestTopicsSensor(ForumEntity):
    """Nombre de sujets actifs ces dernières 24 heures ; liste des derniers sujets."""

    _attr_icon = "mdi:forum"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator, "latest_topics")

    @property
    def native_value(self) -> int:
        return _recent(self.coordinator.data.get("latest", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        cat, tag = self.coordinator.data.get("category"), self.coordinator.data.get("tag")
        if tag and cat:
            url = f"{BASE_URL}/tags/c/{cat.get('slug') or 'c'}/{cat['id']}/{tag}"
        elif tag:
            url = f"{BASE_URL}/tag/{tag}"
        else:
            url = cat["url"] if cat else f"{BASE_URL}/latest"
        return {"topics": self.coordinator.data.get("latest", []), "category": cat, "tag": tag, "forum_url": url}


class MyTopicsSensor(ForumEntity):
    """Nombre de sujets ouverts par le membre ; liste avec réponses et vues."""

    _attr_icon = "mdi:forum-outline"

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator, "my_topics")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("mine", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        username = self.coordinator.username
        return {"topics": self.coordinator.data.get("mine", []), "username": username,
                "forum_url": f"{BASE_URL}/u/{username}/activity/topics"}


class NotificationsSensor(ForumEntity):
    """Notifications non lues du compte relié ; dernières notifications."""

    _attr_icon = "mdi:bell"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator, "notifications")

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("unread") or 0)

    @property
    def icon(self) -> str:
        return "mdi:bell-badge" if self.native_value else "mdi:bell"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"notifications": self.coordinator.data.get("notifications", []), "account": self.coordinator.data.get("account"),
                "forum_url": f"{BASE_URL}/my/notifications"}


class NewsSensor(ForumEntity):
    """Date du dernier article de la rubrique Actualités de hacf.fr ; derniers articles."""

    _attr_icon = "mdi:newspaper-variant-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator, "news")

    @property
    def native_value(self) -> datetime | None:
        for article in self.coordinator.data.get("news", []):
            if when := dt_util.parse_datetime(article.get("published_at") or ""):
                return when
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        news = self.coordinator.data.get("news", [])
        return {"articles": news, "last_title": news[0]["title"] if news else None, "news_url": NEWS_PAGE}


class TopicListSensor(ForumEntity):
    """Liste facultative (populaires, sans réponse, recherche, messages, non lus, suivis, signets) : nombre d'éléments."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForumCoordinator, key: str, data_key: str, icon: str,
                 url: Callable[[dict[str, Any]], str], extra: tuple[str, ...] = (), attr: str = "topics") -> None:
        super().__init__(coordinator, key)
        self._data_key, self._url, self._extra, self._attr = data_key, url, extra, attr
        self._attr_icon = icon

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get(self._data_key) or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.coordinator.data
        attrs = {self._attr: d.get(self._data_key) or [], "forum_url": self._url(d)}
        for k in self._extra:
            attrs[k] = d.get(k)
        return attrs


class MessagesSensor(TopicListSensor):
    """Messages privés : nombre de discussions avec des messages non lus ; liste des discussions."""

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator, "private_messages", "messages", "mdi:email-outline",
                         lambda d: f"{BASE_URL}/u/{d.get('account') or ''}/messages")

    @property
    def native_value(self) -> int:
        return sum(1 for t in self.coordinator.data.get("messages") or [] if t.get("unread"))

    @property
    def icon(self) -> str:
        return "mdi:email-alert" if self.native_value else "mdi:email-outline"


class ValueSensor(ForumEntity):
    """Une valeur du profil ou des statistiques du forum (relues une fois par heure)."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForumCoordinator, key: str, data_key: str, field: str, icon: str) -> None:
        super().__init__(coordinator, key)
        self._data_key, self._field = data_key, field
        self._attr_icon = icon

    @property
    def native_value(self) -> int | None:
        value = (self.coordinator.data.get(self._data_key) or {}).get(self._field)
        return int(value) if isinstance(value, (int, float)) else None


class BadgesSensor(ForumEntity):
    """Nombre de badges du membre ; liste du plus récent au plus ancien."""

    _attr_icon = "mdi:medal"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator, "badges")

    @property
    def native_value(self) -> int | None:
        profile = self.coordinator.data.get("profile")
        return len(profile.get("badges") or []) if profile else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        badges = (self.coordinator.data.get("profile") or {}).get("badges") or []
        return {"badges": badges, "last_badge": badges[0]["name"] if badges else None,
                "forum_url": f"{BASE_URL}/u/{self.coordinator.username}/badges"}


class ContributorsSensor(ForumEntity):
    """Membre le plus aimé de la semaine ; les dix premiers en attribut."""

    _attr_icon = "mdi:trophy"

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator, "top_contributor")

    @property
    def native_value(self) -> str | None:
        top = self.coordinator.data.get("contributors") or []
        return top[0]["username"] if top else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"contributors": self.coordinator.data.get("contributors") or [],
                "forum_url": f"{BASE_URL}/u?period=weekly&order=likes_received"}
