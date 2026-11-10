"""Paramétrage, capteurs, compte relié (clé d'API utilisateur Discourse), réauthentification, diagnostics."""
from __future__ import annotations

import base64
import json
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.hacf_forum.const import DOMAIN
from custom_components.hacf_forum.diagnostics import async_get_config_entry_diagnostics

F = "https://forum.hacf.fr"
SITE = {"categories": [{"id": 8, "name": "Partages", "color": "27ae60", "slug": "partages"},
                       {"id": 12, "name": "Lovelace", "color": "0088cc", "slug": "lovelace", "parent_category_id": 8}]}


def _topic(tid: int, title: str, cat: int = 12, posts: int = 4, poster: str = "Alice") -> dict:
    return {"id": tid, "title": title, "slug": f"sujet-{tid}", "posts_count": posts, "reply_count": posts - 1,
            "highest_post_number": posts, "views": 100, "like_count": 5, "category_id": cat, "visible": True,
            "created_at": "2026-11-01T10:00:00.000Z", "last_posted_at": "2026-11-10T10:00:00.000Z",
            "last_poster_username": poster, "pinned": False, "closed": False, "tags": ["carte"]}


def _list(*topics: dict) -> dict:
    return {"users": [{"username": "Alice", "avatar_template": "/user_avatar/forum.hacf.fr/alice/{size}/1.png"}],
            "topic_list": {"topics": list(topics)}}


NEWS_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:media="http://search.yahoo.com/mrss/" version="2.0"><channel>
<title>Actualités - Home Assistant Communauté Francophone</title>
<item><title><![CDATA[2026.11 : de nombreuses nouveautés !]]></title>
<description><![CDATA[<p>Cet article est une traduction de l&#39;annonce de la version 2026.11.</p>]]></description>
<link>https://www.hacf.fr/ha-2026-11/</link><guid isPermaLink="false">abc</guid><category>Actualités</category>
<dc:creator><![CDATA[jrvrcd]]></dc:creator><pubDate>Fri, 06 Nov 2026 09:52:14 GMT</pubDate>
<media:content url="https://www.hacf.fr/content/images/2026/11/ha-2026-11.png" medium="image"/>
<content:encoded><![CDATA[<p>Texte complet</p>]]></content:encoded></item>
<item><title>Lien externe ignoré</title><link>https://exemple.com/x/</link></item>
<item><title>Community Day 2026</title><link>https://www.hacf.fr/community-day-2026/</link>
<pubDate>Mon, 26 Oct 2026 08:00:00 GMT</pubDate><media:content url="javascript:alert(1)" medium="image"/></item>
</channel></rss>"""


def _mock_public(aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get("https://www.hacf.fr/tag/news/rss/", text=NEWS_RSS)
    aioclient_mock.get(f"{F}/site.json", json=SITE)
    aioclient_mock.get(f"{F}/latest.json", json=_list(_topic(1, "Ma carte météo"), _topic(2, "Zigbee", cat=8)))
    aioclient_mock.get(f"{F}/topics/created-by/Membre.json", json=_list(_topic(10, "Mes cartes", posts=12)))


async def _setup(hass: HomeAssistant, data: dict) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="membre", title="Forum HACF (Membre)", data=data)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow_without_account(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{F}/u/Membre.json", json={"user": {"username": "Membre"}})
    _mock_public(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"username": " @Membre "})
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"next_step_id": "finish"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"username": "Membre"}
    assert result["title"] == "Forum HACF (Membre)"


async def test_unknown_username(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{F}/u/Personne.json", status=404)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"username": "Personne"})
    assert result["errors"] == {"username": "unknown_user"}


async def test_sensors(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    _mock_public(aioclient_mock)
    entry = await _setup(hass, {"username": "Membre"})
    assert entry.state is ConfigEntryState.LOADED
    reg = er.async_get(hass)
    latest = hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_latest_topics"))
    topics = latest.attributes["topics"]
    assert [t["title"] for t in topics] == ["Ma carte météo", "Zigbee"]
    assert topics[0]["category"] == "Partages › Lovelace" and topics[0]["category_color"] == "#0088cc"
    assert topics[0]["url"] == f"{F}/t/sujet-1/1" and topics[0]["last_url"] == f"{F}/t/sujet-1/1/4"
    assert topics[0]["last_poster_avatar"] == f"{F}/user_avatar/forum.hacf.fr/alice/48/1.png"
    mine = hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_my_topics"))
    assert mine.state == "1" and mine.attributes["topics"][0]["replies"] == 11
    # sans compte relié : pas de capteur de notifications
    assert reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_notifications") is None


async def test_link_account(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Le texte chiffré par le forum avec la clé publique est lu par l'intégration."""
    _mock_public(aioclient_mock)
    aioclient_mock.get(f"{F}/session/current.json", json={"current_user": {"username": "Membre", "all_unread_notifications_count": 2}})
    aioclient_mock.get(f"{F}/notifications.json", json={"notifications": []})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"username": ""})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"next_step_id": "account"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "account"
    query = parse_qs(urlparse(result["description_placeholders"]["url"]).query)
    assert query["scopes"] == ["read,notifications,session_info"]
    public = serialization.load_pem_public_key(query["public_key"][0].encode())
    secret = public.encrypt(json.dumps({"key": "cle-du-compte", "nonce": query["nonce"][0], "api": 4}).encode(), padding.PKCS1v15())
    payload = base64.encodebytes(secret).decode()  # avec retours à la ligne, comme sur le forum

    bad = await hass.config_entries.flow.async_configure(result["flow_id"], {"payload": "pas du base64 !"})
    assert bad["errors"] == {"payload": "invalid_payload"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"payload": payload})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["user_api_key"] == "cle-du-compte"
    assert result["data"]["username"] == "Membre" and result["data"]["client_id"] == query["client_id"][0]
    sent = [c for c in aioclient_mock.mock_calls if str(c[1]).endswith("/session/current.json")][-1]
    assert sent[3]["User-Api-Key"] == "cle-du-compte"


async def test_notifications_and_diagnostics(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    _mock_public(aioclient_mock)
    aioclient_mock.get(f"{F}/session/current.json", json={"current_user": {"username": "Membre", "unread_notifications": 1, "unread_high_priority_notifications": 1}})
    aioclient_mock.get(f"{F}/notifications.json", json={"notifications": [
        {"id": 5, "notification_type": 2, "read": False, "topic_id": 10, "slug": "mes-cartes", "post_number": 12,
         "created_at": "2026-11-10T09:00:00.000Z", "data": {"topic_title": "Mes cartes", "display_username": "Bruno"}},
        {"id": 6, "notification_type": 12, "read": True, "created_at": "2026-11-09T09:00:00.000Z",
         "data": {"badge_id": 3, "badge_name": "Membre actif", "badge_slug": "membre-actif"}}]})
    entry = await _setup(hass, {"username": "Membre", "user_api_key": "cle", "client_id": "abc"})
    reg = er.async_get(hass)
    notes = hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_notifications"))
    assert notes.state == "2"
    first, badge = notes.attributes["notifications"]
    assert first["type"] == "replied" and first["user"] == "Bruno" and first["url"] == f"{F}/t/mes-cartes/10/12"
    assert badge["type"] == "granted_badge" and badge["url"] == f"{F}/badges/3/membre-actif"

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["entry"]["data"]["user_api_key"] == "**REDACTED**" and diag["entry"]["data"]["username"] == "**REDACTED**"
    assert diag["counts"]["notifications"] == 2


async def test_refused_key_starts_reauth(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    _mock_public(aioclient_mock)
    aioclient_mock.get(f"{F}/session/current.json", status=403)
    entry = await _setup(hass, {"username": "Membre", "user_api_key": "revoquee", "client_id": "abc"})
    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == "reauth" for f in flows)


async def test_news(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Actualités de hacf.fr : articles du site seulement, liens et images vérifiés."""
    _mock_public(aioclient_mock)
    entry = await _setup(hass, {"username": "Membre"})
    reg = er.async_get(hass)
    news = hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_news"))
    assert news.state == "2026-11-06T09:52:14+00:00"
    first, second = news.attributes["articles"]
    assert first["title"] == "2026.11 : de nombreuses nouveautés !" and first["author"] == "jrvrcd"
    assert first["summary"] == "Cet article est une traduction de l'annonce de la version 2026.11."
    assert first["image"] == "https://www.hacf.fr/content/images/2026/11/ha-2026-11.png"
    assert second["url"] == "https://www.hacf.fr/community-day-2026/" and second["image"] is None
    assert news.attributes["last_title"] == first["title"]


async def test_news_disabled_and_unreachable(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Flux injoignable : le forum reste lisible ; option désactivée : pas de capteur."""
    aioclient_mock.get("https://www.hacf.fr/tag/news/rss/", status=503)
    aioclient_mock.get(f"{F}/site.json", json=SITE)
    aioclient_mock.get(f"{F}/latest.json", json=_list(_topic(1, "Ma carte météo")))
    aioclient_mock.get(f"{F}/topics/created-by/Membre.json", json=_list())
    entry = await _setup(hass, {"username": "Membre"})
    assert entry.state is ConfigEntryState.LOADED
    reg = er.async_get(hass)
    news = hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_news"))
    assert news.state == "unknown" and news.attributes["articles"] == []

    hass.config_entries.async_update_entry(entry, options={"news": False})
    await hass.async_block_till_done()
    assert hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_news")).state == "unavailable"
