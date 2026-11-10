"""Diagnostics : sans la clé du compte, l'identifiant de l'application ni le pseudo."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import ForumConfigEntry
from .const import CONF_CLIENT_ID, CONF_USER_API_KEY, CONF_USERNAME

TO_REDACT = {CONF_USER_API_KEY, CONF_CLIENT_ID, CONF_USERNAME, "title", "unique_id"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ForumConfigEntry) -> dict[str, Any]:
    data = entry.runtime_data.data or {}
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "last_update_success": entry.runtime_data.last_update_success,
        "counts": {
            "latest": len(data.get("latest", [])), "mine": len(data.get("mine", [])),
            "notifications": len(data.get("notifications", [])), "unread": data.get("unread"),
            "news": len(data.get("news", [])),
        },
        "category": data.get("category"),
        "news_error": entry.runtime_data.news_error,
    }
