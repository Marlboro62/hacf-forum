"""Constantes de l'intégration HACF Forum."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "hacf_forum"
VERSION: Final = "0.4.0b2"

BASE_URL: Final = "https://forum.hacf.fr"

CONF_USERNAME: Final = "username"
CONF_USER_API_KEY: Final = "user_api_key"
CONF_CLIENT_ID: Final = "client_id"
CONF_CATEGORY: Final = "category"
CONF_TAG: Final = "tag"
CONF_TOPICS: Final = "topics"
CONF_SCAN_MINUTES: Final = "scan_minutes"
CONF_NEWS: Final = "news"

# Fonctions facultatives, chacune activée par son interrupteur dans les options (toutes désactivées par défaut)
CONF_POPULAR: Final = "popular"
CONF_POPULAR_PERIOD: Final = "popular_period"
CONF_UNANSWERED: Final = "unanswered"
CONF_HIDE_SOLVED: Final = "hide_solved"
CONF_SEARCH: Final = "search"
CONF_POSTS: Final = "latest_posts"
CONF_PROFILE: Final = "profile"
CONF_FORUM_STATS: Final = "forum_stats"
CONF_CONTRIBUTORS: Final = "contributors"
CONF_UNREAD: Final = "unread_new"
CONF_TRACKED: Final = "tracked"
CONF_BOOKMARKS: Final = "bookmarks"
CONF_MESSAGES: Final = "private_messages"
# Interrupteurs : publics, puis réservés au compte relié
PUBLIC_SWITCHES: Final = (CONF_POPULAR, CONF_UNANSWERED, CONF_HIDE_SOLVED, CONF_POSTS, CONF_PROFILE, CONF_FORUM_STATS, CONF_CONTRIBUTORS)
ACCOUNT_SWITCHES: Final = (CONF_UNREAD, CONF_TRACKED, CONF_BOOKMARKS, CONF_MESSAGES)
PERIODS: Final = ("daily", "weekly", "monthly", "yearly")
DEFAULT_POPULAR_PERIOD: Final = "weekly"
# Profil, statistiques du forum et meilleurs contributeurs : relus une fois par heure
SLOW_HOURS: Final = 1

DEFAULT_TOPICS: Final = 20
DEFAULT_SCAN_MINUTES: Final = 10
MIN_SCAN_MINUTES: Final = 5
DEFAULT_NEWS: Final = True
# Actualités de hacf.fr : quelques articles par mois, flux relu toutes les 3 heures
NEWS_HOURS: Final = 3
NEWS_ITEMS: Final = 15

# Fichier de la carte, servi par Home Assistant et chargé dans l'interface
CARD_URL: Final = f"/{DOMAIN}/hacf-forum-card.js"
CARD_FILE: Final = "frontend/hacf-forum-card.js"

# Droits demandés au forum pour les notifications : lecture seule
USER_API_SCOPES: Final = "read,notifications,session_info"
APPLICATION_NAME: Final = "Home Assistant (HACF Forum)"
