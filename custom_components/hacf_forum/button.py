"""Bouton « Actualiser » : relit le forum tout de suite, sans attendre la prochaine mise à jour."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ForumConfigEntry
from .coordinator import ForumCoordinator
from .sensor import device_info


async def async_setup_entry(hass: HomeAssistant, entry: ForumConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([RefreshButton(entry.runtime_data)])


class RefreshButton(CoordinatorEntity[ForumCoordinator], ButtonEntity):
    """Relit le forum maintenant, profil et statistiques compris (lus sinon une fois par heure)."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: ForumCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_refresh"
        self._attr_device_info = device_info(coordinator)

    async def async_press(self) -> None:
        await self.coordinator.async_refresh_now()
