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


async def test_tag_alone_and_in_category(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Étiquette suivie (issue du fil HACF : « ia ») : seule, puis dans une catégorie ; saisie normalisée."""
    _mock_public(aioclient_mock)
    aioclient_mock.get(f"{F}/tags.json", json={"tags": [{"id": "ia", "name": "ia", "count": 40},
                                                        {"id": "zigbee", "name": "zigbee", "count": 90}]})
    aioclient_mock.get(f"{F}/tag/ia/l/latest.json", json=_list(_topic(5, "Assist et LLM")))
    aioclient_mock.get(f"{F}/tags/c/lovelace/12/ia/l/latest.json", json=_list(_topic(6, "Carte Assist")))
    entry = await _setup(hass, {"username": "Membre"})
    reg = er.async_get(hass)
    sensor_id = reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_latest_topics")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "settings"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"category": "0", "tag": " #IA "})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["tag"] == "ia" and entry.options["category"] == ""
    await hass.async_block_till_done()
    state = hass.states.get(sensor_id)
    assert [t["title"] for t in state.attributes["topics"]] == ["Assist et LLM"]
    assert state.attributes["tag"] == "ia" and state.attributes["forum_url"] == f"{F}/tag/ia"

    hass.config_entries.async_update_entry(entry, options={**entry.options, "category": "12"})
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get(sensor_id)
    assert [t["title"] for t in state.attributes["topics"]] == ["Carte Assist"]
    assert state.attributes["forum_url"] == f"{F}/tags/c/lovelace/12/ia"


async def test_optional_features(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Fonctions facultatives : désactivées par défaut, un capteur chacune une fois l'interrupteur activé."""
    solved = {**_topic(3, "Résolu", posts=2), "has_accepted_answer": True}
    aioclient_mock.get("https://www.hacf.fr/tag/news/rss/", text=NEWS_RSS)
    aioclient_mock.get(f"{F}/site.json", json=SITE)
    aioclient_mock.get(f"{F}/latest.json", json=_list(_topic(1, "Ma carte météo"), _topic(2, "Sans réponse", posts=1), solved))
    aioclient_mock.get(f"{F}/topics/created-by/Membre.json", json=_list(_topic(10, "Mes cartes", posts=12)))
    aioclient_mock.get(f"{F}/top.json?period=monthly", json=_list(_topic(7, "Le plus lu")))
    aioclient_mock.get(f"{F}/search.json?q=linky%20order%3Alatest", json={
        "topics": [{"id": 8, "title": "Linky et Tempo", "slug": "linky-tempo", "posts_count": 3, "category_id": 12}],
        "posts": [{"topic_id": 8, "post_number": 2, "username": "Alice", "created_at": "2026-11-10T10:00:00.000Z",
                   "blurb": "<b>Linky</b> en mode Tempo", "avatar_template": "/a/{size}.png"}]})
    aioclient_mock.get(f"{F}/posts.json", json={"latest_posts": [
        {"id": 50, "topic_id": 1, "topic_slug": "sujet-1", "topic_title": "Ma carte météo", "post_number": 4,
         "username": "Alice", "created_at": "2026-11-10T10:00:00.000Z", "cooked": "<p>Merci, ça marche !</p>", "category_id": 12}]})
    aioclient_mock.get(f"{F}/u/Membre/summary.json", json={"user_summary": {
        "likes_received": 120, "likes_given": 80, "post_count": 300, "topic_count": 12, "days_visited": 200, "solved_count": 9}})
    aioclient_mock.get(f"{F}/u/Membre.json", json={"user": {"username": "Membre", "trust_level": 2}})
    aioclient_mock.get(f"{F}/user-badges/Membre.json", json={
        "badges": [{"id": 1, "name": "Premier j'aime", "slug": "premier-j-aime"}, {"id": 2, "name": "Solution", "slug": "solution"}],
        "user_badges": [{"badge_id": 1, "granted_at": "2026-01-01T00:00:00Z"}, {"badge_id": 2, "granted_at": "2026-06-01T00:00:00Z"}]})
    aioclient_mock.get(f"{F}/about.json", json={"about": {"stats": {
        "users_count": 9000, "active_users_7_days": 700, "topics_count": 30000, "posts_count": 250000}}})
    aioclient_mock.get(f"{F}/directory_items.json?period=weekly&order=likes_received", json={"directory_items": [
        {"likes_received": 40, "post_count": 30, "user": {"username": "Bruno", "avatar_template": "/b/{size}.png"}}]})
    entry = await _setup(hass, {"username": "Membre"})
    reg = er.async_get(hass)
    assert reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_popular_topics") is None

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "features"})
    assert result["type"] is FlowResultType.FORM and "unread_new" not in result["data_schema"].schema
    result = await hass.config_entries.options.async_configure(result["flow_id"], {
        "popular": True, "popular_period": "monthly", "unanswered": True, "hide_solved": True, "latest_posts": True,
        "profile": True, "forum_stats": True, "contributors": True, "search": " linky "})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    def state(key: str):
        return hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{key}"))

    latest = state("latest_topics").attributes["topics"]
    assert [t["title"] for t in latest] == ["Ma carte météo", "Sans réponse"]  # résolu masqué
    assert [t["title"] for t in state("unanswered_topics").attributes["topics"]] == ["Sans réponse"]
    assert state("popular_topics").attributes["topics"][0]["title"] == "Le plus lu"
    assert state("popular_topics").attributes["popular_period"] == "monthly"
    found = state("search_results").attributes["topics"][0]
    assert found["title"] == "Linky et Tempo" and found["url"] == f"{F}/t/linky-tempo/8/2" and found["excerpt"] == "Linky en mode Tempo"
    post = state("latest_posts").attributes["posts"][0]
    assert post["url"] == f"{F}/t/sujet-1/1/4" and post["excerpt"] == "Merci, ça marche !"
    assert state("likes_received").state == "120" and state("solutions").state == "9" and state("trust_level").state == "2"
    assert state("badges").state == "2" and state("badges").attributes["last_badge"] == "Solution"
    assert state("forum_members").state == "9000" and state("forum_active_users").state == "700"
    assert state("top_contributor").state == "Bruno"


async def test_account_features(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Avec le compte relié : non lus et nouveaux, suivis, signets, messages privés (clé envoyée)."""
    # avant /latest.json : le simulateur prend la première adresse qui correspond
    aioclient_mock.get(f"{F}/latest.json?f=tracked", json=_list(_topic(22, "Suivi")))
    _mock_public(aioclient_mock)
    aioclient_mock.get(f"{F}/session/current.json", json={"current_user": {"username": "Membre", "all_unread_notifications_count": 0}})
    aioclient_mock.get(f"{F}/notifications.json", json={"notifications": []})
    aioclient_mock.get(f"{F}/unread.json", json=_list({**_topic(20, "Non lu", posts=6), "last_read_post_number": 4}))
    aioclient_mock.get(f"{F}/new.json", json=_list({**_topic(21, "Tout neuf", posts=1), "unseen": True}))
    aioclient_mock.get(f"{F}/u/Membre/bookmarks.json", json={"user_bookmark_list": {"bookmarks": [
        {"id": 1, "title": "Carte météo", "name": "À relire", "bookmarkable_url": "/t/carte/30/2",
         "created_at": "2026-11-01T10:00:00.000Z", "reminder_at": "2099-01-01T10:00:00.000Z"}]}})
    aioclient_mock.get(f"{F}/topics/private-messages/Membre.json", json=_list(
        {**_topic(40, "Question privée", posts=3), "last_read_post_number": 1}, {**_topic(41, "Lu", posts=2), "last_read_post_number": 2}))
    entry = MockConfigEntry(domain=DOMAIN, unique_id="membre", title="Forum HACF (Membre)",
                            data={"username": "Membre", "user_api_key": "cle", "client_id": "abc"},
                            options={"unread_new": True, "tracked": True, "bookmarks": True, "private_messages": True})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    reg = er.async_get(hass)

    def state(key: str):
        return hass.states.get(reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{key}"))

    assert state("unread_topics").state == "1" and state("unread_topics").attributes["topics"][0]["unread"] == 2
    assert state("new_topics").attributes["topics"][0]["unread"] == 1
    assert state("tracked_topics").attributes["topics"][0]["title"] == "Suivi"
    mark = state("bookmarks").attributes["bookmarks"][0]
    assert mark["url"] == f"{F}/t/carte/30/2" and mark["name"] == "À relire"
    assert state("private_messages").state == "1"
    sent = [c for c in aioclient_mock.mock_calls if str(c[1]).endswith("/unread.json")][-1]
    assert sent[3]["User-Api-Key"] == "cle"


async def test_refresh_button(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Bouton Actualiser : le forum est relu tout de suite, profil compris (sinon une fois par heure)."""
    _mock_public(aioclient_mock)
    aioclient_mock.get(f"{F}/u/Membre/summary.json", json={"user_summary": {"likes_received": 1}})
    aioclient_mock.get(f"{F}/u/Membre.json", json={"user": {"username": "Membre", "trust_level": 1}})
    aioclient_mock.get(f"{F}/user-badges/Membre.json", json={"badges": [], "user_badges": []})
    entry = MockConfigEntry(domain=DOMAIN, unique_id="membre", title="Forum HACF (Membre)",
                            data={"username": "Membre"}, options={"profile": True})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    reg = er.async_get(hass)
    button = reg.async_get_entity_id("button", DOMAIN, f"{entry.entry_id}_refresh")
    assert button is not None

    def calls(path: str) -> int:
        return sum(1 for c in aioclient_mock.mock_calls if str(c[1]).endswith(path))

    latest, summary = calls("/latest.json"), calls("/summary.json")
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert calls("/latest.json") == latest + 1 and calls("/summary.json") == summary + 1
