"""Capteurs : derniers sujets, mes sujets, notifications non lues (listes en attributs pour la carte)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import ForumConfigEntry
from .const import BASE_URL, DOMAIN, VERSION
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
    async_add_entities(entities)


class ForumEntity(CoordinatorEntity[ForumCoordinator], SensorEntity):
    _attr_has_entity_name = True
    # listes destinées à la carte : pas d'historique dans la base de Home Assistant
    _unrecorded_attributes = frozenset({"topics", "notifications", "category", "articles"})

    def __init__(self, coordinator: ForumCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="HACF (non officiel)",
            model="Forum Discourse",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=BASE_URL,
        )


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
        cat = self.coordinator.data.get("category")
        return {"topics": self.coordinator.data.get("latest", []), "category": cat, "forum_url": cat["url"] if cat else f"{BASE_URL}/latest"}


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
