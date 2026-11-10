"""Client du forum HACF (Discourse) : sujets publics et, avec une clé de compte, notifications."""
from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

import aiohttp

from .const import BASE_URL, VERSION
from .news import NEWS_FEED

# Flux des actualités : plusieurs centaines de Ko (articles complets) ; au-delà de 8 Mo, refusé
NEWS_MAX_BYTES = 8 * 1024 * 1024


class ForumError(Exception):
    """Forum injoignable ou réponse illisible."""


class ForumAuthError(ForumError):
    """Clé du compte refusée (révoquée ou expirée)."""


class ForumNotFound(ForumError):
    """Pseudo ou catégorie introuvable."""


class ForumClient:
    """Lecture de l'API JSON de Discourse."""

    def __init__(
        self, session: aiohttp.ClientSession, user_api_key: str | None = None, client_id: str | None = None
    ) -> None:
        self._session = session
        self._key = user_api_key
        self._client_id = client_id

    @property
    def has_key(self) -> bool:
        return bool(self._key)

    async def _get(self, path: str, auth: bool = False) -> dict[str, Any]:
        headers = {"Accept": "application/json", "User-Agent": f"HomeAssistant-HACF-Forum/{VERSION}"}
        if auth:
            if not self._key:
                raise ForumAuthError("aucune clé de compte")
            headers["User-Api-Key"] = self._key
            if self._client_id:
                headers["User-Api-Client-Id"] = self._client_id
        try:
            async with asyncio.timeout(20):
                resp = await self._session.get(f"{BASE_URL}{path}", headers=headers)
                if resp.status in (401, 403) and auth:
                    raise ForumAuthError(f"HTTP {resp.status}")
                if resp.status == 404:
                    raise ForumNotFound(path)
                if resp.status != 200:
                    raise ForumError(f"HTTP {resp.status} sur {path}")
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise ForumError(f"{type(err).__name__} sur {path}") from err

    async def latest(self, category_id: int | None = None) -> dict[str, Any]:
        """Derniers sujets actifs, de tout le forum ou d'une catégorie."""
        path = f"/c/{int(category_id)}/l/latest.json" if category_id else "/latest.json"
        return await self._get(path)

    async def created_by(self, username: str) -> dict[str, Any]:
        """Sujets ouverts par un membre."""
        return await self._get(f"/topics/created-by/{quote(username)}.json")

    async def user(self, username: str) -> dict[str, Any]:
        """Profil public d'un membre (vérifie le pseudo)."""
        return await self._get(f"/u/{quote(username)}.json")

    async def site(self) -> dict[str, Any]:
        """Catégories du forum (noms, couleurs, parents)."""
        return await self._get("/site.json")

    async def current_user(self) -> dict[str, Any]:
        """Membre connecté par la clé, avec ses compteurs de notifications."""
        data = await self._get("/session/current.json", auth=True)
        if not isinstance(data.get("current_user"), dict):
            raise ForumAuthError("session absente")
        return data["current_user"]

    async def notifications(self) -> dict[str, Any]:
        """Notifications du membre connecté."""
        return await self._get("/notifications.json", auth=True)

    async def news_feed(self, etag: str | None = None, modified: str | None = None) -> tuple[bytes | None, str | None, str | None]:
        """Flux RSS des actualités de hacf.fr ; None si inchangé depuis la dernière lecture (HTTP 304)."""
        headers = {"Accept": "application/rss+xml, application/xml", "User-Agent": f"HomeAssistant-HACF-Forum/{VERSION}"}
        if etag:
            headers["If-None-Match"] = etag
        if modified:
            headers["If-Modified-Since"] = modified
        try:
            async with asyncio.timeout(30):
                resp = await self._session.get(NEWS_FEED, headers=headers)
                if resp.status == 304:
                    return None, etag, modified
                if resp.status != 200:
                    raise ForumError(f"HTTP {resp.status} sur le flux des actualités")
                body = await resp.content.read(NEWS_MAX_BYTES + 1)
                if len(body) > NEWS_MAX_BYTES:
                    raise ForumError("flux des actualités trop volumineux")
                return body, resp.headers.get("ETag"), resp.headers.get("Last-Modified")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ForumError(f"{type(err).__name__} sur le flux des actualités") from err
