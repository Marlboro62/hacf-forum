"""Paramétrage de HACF Forum : pseudo, compte (notifications, facultatif), catégorie suivie."""
from __future__ import annotations

import base64
from collections.abc import Mapping
import json
import logging
import secrets
from typing import Any
from urllib.parse import urlencode
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ForumAuthError, ForumClient, ForumError, ForumNotFound
from .const import (
    APPLICATION_NAME,
    BASE_URL,
    CONF_CATEGORY,
    CONF_CLIENT_ID,
    CONF_NEWS,
    CONF_SCAN_MINUTES,
    CONF_TOPICS,
    CONF_USER_API_KEY,
    CONF_USERNAME,
    DEFAULT_NEWS,
    DEFAULT_SCAN_MINUTES,
    DEFAULT_TOPICS,
    DOMAIN,
    MIN_SCAN_MINUTES,
    USER_API_SCOPES,
)

_LOGGER = logging.getLogger(__name__)
CONF_PAYLOAD = "payload"


class AccountLink:
    """Autorisation du compte par le forum (clé d'API utilisateur Discourse).

    Home Assistant crée une paire de clés RSA ; le forum chiffre la clé du compte avec la clé publique
    et l'affiche après « Autoriser » ; seule la clé privée, gardée en mémoire pendant le paramétrage,
    permet de la lire.
    """

    def __init__(self) -> None:
        self.client_id = uuid.uuid4().hex
        self.nonce = secrets.token_hex(16)
        self._private: rsa.RSAPrivateKey | None = None
        self.url = ""

    def prepare(self) -> None:
        """Clés RSA et adresse de la page « Autoriser » (appel bloquant : exécuteur)."""
        self._private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = self._private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        query = urlencode({
            "application_name": APPLICATION_NAME, "client_id": self.client_id, "scopes": USER_API_SCOPES,
            "public_key": public, "nonce": self.nonce,
        })
        self.url = f"{BASE_URL}/user-api-key/new?{query}"

    def decrypt(self, payload: str) -> str:
        """Clé du compte, lue dans le texte affiché par le forum ; ValueError si illisible."""
        if self._private is None:
            raise ValueError("clés absentes")
        raw = base64.b64decode("".join(payload.split()), validate=False)
        data = json.loads(self._private.decrypt(raw, padding.PKCS1v15()))
        if data.get("nonce") != self.nonce or not data.get("key"):
            raise ValueError("réponse d'une autre demande")
        return str(data["key"])


async def _check_account(hass: HomeAssistant, key: str, client_id: str) -> str:
    """Pseudo du compte relié par la clé."""
    me = await ForumClient(async_get_clientsession(hass), key, client_id).current_user()
    return str(me.get("username") or "")


class AccountSteps:
    """Étapes communes au paramétrage, aux options et à la réauthentification."""

    _link: AccountLink | None = None

    async def _account_form(self, step_id: str, user_input: dict[str, Any] | None) -> tuple[dict[str, Any] | None, Any]:
        """Formulaire du texte à coller ; rend (données du compte, formulaire à afficher)."""
        errors: dict[str, str] = {}
        if self._link is None or user_input is None and not self._link.url:
            self._link = AccountLink()
            await self.hass.async_add_executor_job(self._link.prepare)  # type: ignore[attr-defined]
        if user_input is not None:
            try:
                key = await self.hass.async_add_executor_job(self._link.decrypt, user_input[CONF_PAYLOAD])  # type: ignore[attr-defined]
                username = await _check_account(self.hass, key, self._link.client_id)  # type: ignore[attr-defined]
            except (ValueError, TypeError) as err:
                _LOGGER.debug("Texte du forum illisible : %s", type(err).__name__)
                errors[CONF_PAYLOAD] = "invalid_payload"
            except ForumAuthError:
                errors["base"] = "invalid_auth"
            except ForumError:
                errors["base"] = "cannot_connect"
            else:
                return {CONF_USER_API_KEY: key, CONF_CLIENT_ID: self._link.client_id, CONF_USERNAME: username}, None
        form = self.async_show_form(  # type: ignore[attr-defined]
            step_id=step_id,
            data_schema=vol.Schema({vol.Required(CONF_PAYLOAD): selector.TextSelector(selector.TextSelectorConfig(multiline=True))}),
            description_placeholders={"url": self._link.url},
            errors=errors,
        )
        return None, form


class HacfForumConfigFlow(AccountSteps, ConfigFlow, domain=DOMAIN):
    """Ajout de l'intégration."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HacfForumOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Pseudo HACF (facultatif) pour « Mes sujets »."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = (user_input.get(CONF_USERNAME) or "").strip().lstrip("@")
            if username:
                try:
                    await ForumClient(async_get_clientsession(self.hass)).user(username)
                except ForumNotFound:
                    errors[CONF_USERNAME] = "unknown_user"
                except ForumError:
                    errors["base"] = "cannot_connect"
            else:
                try:
                    await ForumClient(async_get_clientsession(self.hass)).latest()
                except ForumError:
                    errors["base"] = "cannot_connect"
            if not errors:
                self._data = {CONF_USERNAME: username}
                return await self.async_step_menu()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Optional(CONF_USERNAME, default=""): str}),
            errors=errors,
        )

    async def async_step_menu(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Relier le compte (notifications) ou terminer."""
        return self.async_show_menu(step_id="menu", menu_options=["account", "finish"])

    async def async_step_account(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Autorisation du compte sur le forum, puis texte à coller."""
        account, form = await self._account_form("account", user_input)
        if account is None:
            return form
        self._data.update(account)
        return await self.async_step_finish()

    async def async_step_finish(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        username = self._data.get(CONF_USERNAME) or ""
        await self.async_set_unique_id((username or "public").lower())
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=f"Forum HACF ({username})" if username else "Forum HACF", data=self._data)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Clé du compte refusée : nouvelle autorisation."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        account, form = await self._account_form("reauth_confirm", user_input)
        if account is None:
            return form
        entry = self._get_reauth_entry()
        account[CONF_USERNAME] = entry.data.get(CONF_USERNAME) or account[CONF_USERNAME]
        return self.async_update_reload_and_abort(entry, data_updates=account)


class HacfForumOptionsFlow(AccountSteps, OptionsFlow):
    """Catégorie suivie, nombre de sujets, fréquence ; relier ou délier le compte."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        has_key = bool(self.config_entry.data.get(CONF_USER_API_KEY))
        return self.async_show_menu(step_id="init", menu_options=["settings", "unlink" if has_key else "account"])

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            user_input[CONF_CATEGORY] = "" if user_input.get(CONF_CATEGORY) in (None, "0") else user_input[CONF_CATEGORY]
            return self.async_create_entry(data={**self.config_entry.options, **user_input})
        coordinator = getattr(self.config_entry, "runtime_data", None)
        cats = await coordinator.categories() if coordinator else {}
        choices = [selector.SelectOptionDict(value="0", label="—")] + [
            selector.SelectOptionDict(value=str(c["id"]), label=c["full_name"])
            for c in sorted(cats.values(), key=lambda c: c["full_name"].lower())
        ]
        opts = self.config_entry.options
        schema = vol.Schema({
            vol.Optional(CONF_CATEGORY, default=str(opts.get(CONF_CATEGORY) or "0")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=choices, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional(CONF_TOPICS, default=int(opts.get(CONF_TOPICS, DEFAULT_TOPICS))): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=50, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_SCAN_MINUTES, default=int(opts.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES))): selector.NumberSelector(
                selector.NumberSelectorConfig(min=MIN_SCAN_MINUTES, max=120, step=1, mode=selector.NumberSelectorMode.BOX,
                                              unit_of_measurement="min")
            ),
            vol.Optional(CONF_NEWS, default=bool(opts.get(CONF_NEWS, DEFAULT_NEWS))): selector.BooleanSelector(),
        })
        return self.async_show_form(step_id="settings", data_schema=schema)

    async def async_step_account(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        account, form = await self._account_form("account", user_input)
        if account is None:
            return form
        if self.config_entry.data.get(CONF_USERNAME):
            account[CONF_USERNAME] = self.config_entry.data[CONF_USERNAME]
        self.hass.config_entries.async_update_entry(self.config_entry, data={**self.config_entry.data, **account})
        self.hass.config_entries.async_schedule_reload(self.config_entry.entry_id)
        return self.async_create_entry(data=dict(self.config_entry.options))

    async def async_step_unlink(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Délier le compte : la clé est oubliée (à révoquer aussi dans le profil du forum)."""
        if user_input is not None:
            data = {k: v for k, v in self.config_entry.data.items() if k not in (CONF_USER_API_KEY, CONF_CLIENT_ID)}
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            self.hass.config_entries.async_schedule_reload(self.config_entry.entry_id)
            return self.async_create_entry(data=dict(self.config_entry.options))
        return self.async_show_form(step_id="unlink", data_schema=vol.Schema({}))
