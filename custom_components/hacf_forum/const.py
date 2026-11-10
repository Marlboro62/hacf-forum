"""Constantes de l'intégration HACF Forum."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "hacf_forum"
VERSION: Final = "0.1.0b3"

BASE_URL: Final = "https://forum.hacf.fr"

CONF_USERNAME: Final = "username"
CONF_USER_API_KEY: Final = "user_api_key"
CONF_CLIENT_ID: Final = "client_id"
CONF_CATEGORY: Final = "category"
CONF_TOPICS: Final = "topics"
CONF_SCAN_MINUTES: Final = "scan_minutes"

DEFAULT_TOPICS: Final = 20
DEFAULT_SCAN_MINUTES: Final = 10
MIN_SCAN_MINUTES: Final = 5

# Fichier de la carte, servi par Home Assistant et chargé dans l'interface
CARD_URL: Final = f"/{DOMAIN}/hacf-forum-card.js"
CARD_FILE: Final = "frontend/hacf-forum-card.js"

# Droits demandés au forum pour les notifications : lecture seule
USER_API_SCOPES: Final = "read,notifications,session_info"
APPLICATION_NAME: Final = "Home Assistant (HACF Forum)"
