"""HACF Forum : sujets et notifications du forum de la communauté francophone de Home Assistant.

© 2026 Marlboro62. Tous droits réservés : copie, diffusion et modification interdites sans accord écrit (voir LICENSE).
"""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_COMPONENT_LOADED, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import ForumClient
from .const import CARD_FILE, CARD_URL, CONF_CLIENT_ID, CONF_USER_API_KEY, DOMAIN, VERSION
from .coordinator import ForumCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type ForumConfigEntry = ConfigEntry[ForumCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Carte du forum servie par Home Assistant et chargée dans l'interface : rien à ajouter à la main."""
    if hass.http is None:
        _LOGGER.debug("Interface web absente : la carte n'est pas chargée")
        return True
    from homeassistant.components.http import StaticPathConfig

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(Path(__file__).parent / CARD_FILE), cache_headers=False)]
    )
    if "frontend" in hass.config.components:
        _add_card(hass)
    else:
        # au démarrage, l'interface peut se charger après l'intégration : la carte est ajoutée dès qu'elle est prête
        @callback
        def _frontend_loaded(event: Event) -> None:
            if event.data.get("component") == "frontend":
                _add_card(hass)
                unsub()

        unsub = hass.bus.async_listen(EVENT_COMPONENT_LOADED, _frontend_loaded)
    return True


@callback
def _add_card(hass: HomeAssistant) -> None:
    from homeassistant.components.frontend import add_extra_js_url

    add_extra_js_url(hass, f"{CARD_URL}?v={VERSION}")
    _LOGGER.debug("Carte du forum chargée : %s", CARD_URL)


async def async_setup_entry(hass: HomeAssistant, entry: ForumConfigEntry) -> bool:
    client = ForumClient(async_get_clientsession(hass), entry.data.get(CONF_USER_API_KEY), entry.data.get(CONF_CLIENT_ID))
    coordinator = ForumCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _reload(hass: HomeAssistant, entry: ForumConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ForumConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
