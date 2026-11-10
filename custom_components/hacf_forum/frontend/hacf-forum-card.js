/*
 * Carte Forum HACF — custom:hacf-forum-card
 *
 * Affiche les capteurs de l'intégration HACF Forum (non officielle) : derniers sujets du forum de la
 * communauté francophone de Home Assistant, sujets du membre et notifications du compte relié.
 * Chargée automatiquement par l'intégration : aucune ressource à ajouter.
 */
(() => {
const CARD_VERSION = "0.1.0b1";
const FORUM = "https://forum.hacf.fr";

const DEFAULTS = {
  title: "",
  show_latest: true,
  show_mine: true,
  show_notifications: true,
  max_items: 10,
  show_avatars: true,
  theme: "v2",
  language: "auto",
};

/* ---------------------------------------------------------------- textes */

const I18N = {
  fr: {
    title: "Forum HACF", all: "Tout le forum", latest: "Sujets", mine: "Mes sujets", notifs: "Notifications",
    open: "Ouvrir le forum", seen: "Tout marquer comme vu", none_latest: "Aucun sujet pour le moment.",
    none_mine: "Aucun sujet ouvert par ce pseudo.", none_notifs: "Aucune notification.", unread: "non lues",
    news: "nouveaux", new_badge: "nouveau", replies: "réponses", reply: "réponse", views: "vues", likes: "j'aime",
    by: "par", updated: "Mis à jour", unofficial: "Intégration non officielle",
    missing: "Intégration HACF Forum introuvable", missing_hint: "Ajoutez-la dans Paramètres › Appareils et services › Ajouter une intégration › HACF Forum.",
    no_account: "Reliez votre compte HACF pour voir vos notifications : Paramètres › Appareils et services › HACF Forum › Configurer.",
    pinned: "Épinglé", closed: "Fermé", solved: "Résolu",
    n: {
      mentioned: "{u} vous a mentionné", replied: "{u} a répondu", quoted: "{u} vous a cité", edited: "{u} a modifié votre message",
      liked: "{u} a aimé votre message", liked_consolidated: "{c} j'aime sur vos messages", private_message: "Message privé de {u}",
      invited_to_private_message: "{u} vous invite à une discussion privée", invitee_accepted: "{u} a accepté votre invitation",
      posted: "{u} a publié", moved_post: "{u} a déplacé votre message", linked: "{u} a mis un lien vers votre message",
      granted_badge: "Badge obtenu : {b}", invited_to_topic: "{u} vous invite à un sujet", group_mentioned: "{u} a mentionné votre groupe",
      group_message_summary: "Nouveaux messages de groupe", watching_first_post: "Nouveau sujet", topic_reminder: "Rappel de sujet",
      post_approved: "Votre message a été approuvé", bookmark_reminder: "Rappel de signet", reaction: "{u} a réagi à votre message",
      watching_category_or_tag: "Nouveau message", other: "Notification",
    },
  },
  en: {
    title: "HACF forum", all: "Whole forum", latest: "Topics", mine: "My topics", notifs: "Notifications",
    open: "Open the forum", seen: "Mark all as seen", none_latest: "No topics yet.",
    none_mine: "No topics opened by this user.", none_notifs: "No notifications.", unread: "unread",
    news: "new", new_badge: "new", replies: "replies", reply: "reply", views: "views", likes: "likes",
    by: "by", updated: "Updated", unofficial: "Unofficial integration",
    missing: "HACF Forum integration not found", missing_hint: "Add it in Settings › Devices & services › Add integration › HACF Forum.",
    no_account: "Link your HACF account to see your notifications: Settings › Devices & services › HACF Forum › Configure.",
    pinned: "Pinned", closed: "Closed", solved: "Solved",
    n: {
      mentioned: "{u} mentioned you", replied: "{u} replied", quoted: "{u} quoted you", edited: "{u} edited your post",
      liked: "{u} liked your post", liked_consolidated: "{c} likes on your posts", private_message: "Private message from {u}",
      invited_to_private_message: "{u} invited you to a private conversation", invitee_accepted: "{u} accepted your invitation",
      posted: "{u} posted", moved_post: "{u} moved your post", linked: "{u} linked to your post",
      granted_badge: "Badge earned: {b}", invited_to_topic: "{u} invited you to a topic", group_mentioned: "{u} mentioned your group",
      group_message_summary: "New group messages", watching_first_post: "New topic", topic_reminder: "Topic reminder",
      post_approved: "Your post was approved", bookmark_reminder: "Bookmark reminder", reaction: "{u} reacted to your post",
      watching_category_or_tag: "New post", other: "Notification",
    },
  },
  pl: {
    title: "Forum HACF", all: "Całe forum", latest: "Tematy", mine: "Moje tematy", notifs: "Powiadomienia",
    open: "Otwórz forum", seen: "Oznacz wszystko jako przejrzane", none_latest: "Brak tematów.",
    none_mine: "Brak tematów tego użytkownika.", none_notifs: "Brak powiadomień.", unread: "nieprzeczytane",
    news: "nowe", new_badge: "nowe", replies: "odpowiedzi", reply: "odpowiedź", views: "wyświetleń", likes: "polubień",
    by: "przez", updated: "Zaktualizowano", unofficial: "Integracja nieoficjalna",
    missing: "Nie znaleziono integracji HACF Forum", missing_hint: "Dodaj ją w Ustawienia › Urządzenia i usługi › Dodaj integrację › HACF Forum.",
    no_account: "Połącz konto HACF, aby widzieć powiadomienia: Ustawienia › Urządzenia i usługi › HACF Forum › Konfiguruj.",
    pinned: "Przypięty", closed: "Zamknięty", solved: "Rozwiązany",
    n: {
      mentioned: "{u} wspomniał o Tobie", replied: "{u} odpowiedział", quoted: "{u} zacytował Cię", edited: "{u} edytował Twój post",
      liked: "{u} polubił Twój post", liked_consolidated: "{c} polubień Twoich postów", private_message: "Wiadomość prywatna od {u}",
      invited_to_private_message: "{u} zaprosił Cię do prywatnej rozmowy", invitee_accepted: "{u} przyjął zaproszenie",
      posted: "{u} opublikował", moved_post: "{u} przeniósł Twój post", linked: "{u} dodał link do Twojego postu",
      granted_badge: "Zdobyta odznaka: {b}", invited_to_topic: "{u} zaprosił Cię do tematu", group_mentioned: "{u} wspomniał o Twojej grupie",
      group_message_summary: "Nowe wiadomości grupy", watching_first_post: "Nowy temat", topic_reminder: "Przypomnienie o temacie",
      post_approved: "Twój post został zatwierdzony", bookmark_reminder: "Przypomnienie zakładki", reaction: "{u} zareagował na Twój post",
      watching_category_or_tag: "Nowy post", other: "Powiadomienie",
    },
  },
};

const N_ICON = {
  mentioned: "mdi:at", group_mentioned: "mdi:account-group", replied: "mdi:reply", quoted: "mdi:format-quote-close",
  edited: "mdi:pencil", liked: "mdi:heart", liked_consolidated: "mdi:heart-multiple", reaction: "mdi:emoticon-happy-outline",
  private_message: "mdi:email", invited_to_private_message: "mdi:email-plus", group_message_summary: "mdi:email-multiple",
  invitee_accepted: "mdi:account-check", posted: "mdi:message-text", moved_post: "mdi:arrow-right-bold",
  linked: "mdi:link-variant", granted_badge: "mdi:medal", invited_to_topic: "mdi:account-plus",
  watching_first_post: "mdi:new-box", watching_category_or_tag: "mdi:message-badge", topic_reminder: "mdi:alarm",
  bookmark_reminder: "mdi:bookmark", post_approved: "mdi:check-decagram", other: "mdi:bell",
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// liens : seulement vers le forum (les données viennent du forum, mais on ne fait confiance qu'à son adresse)
const safeUrl = (u) => (typeof u === "string" && u.startsWith(FORUM + "/") ? u : FORUM);
const safeColor = (c) => (/^#[0-9a-f]{3,8}$/i.test(String(c || "")) ? c : "#8fa0b8");
const safeImg = (u) => (typeof u === "string" && /^https:\/\/[^\s"'<>]+$/.test(u) ? u : "");

const store = {
  get(k, d) { try { const v = JSON.parse(window.localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } },
  set(k, v) { try { window.localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* stockage indisponible */ } },
};

class HacfForumCard extends HTMLElement {
  static getStubConfig() {
    return {};
  }

  /** Éditeur visuel : formulaire de Home Assistant. */
  static getConfigForm() {
    return {
      schema: [
        { name: "title", selector: { text: {} } },
        { type: "grid", name: "", schema: [
          { name: "show_latest", selector: { boolean: {} } },
          { name: "show_mine", selector: { boolean: {} } },
          { name: "show_notifications", selector: { boolean: {} } },
          { name: "show_avatars", selector: { boolean: {} } },
        ] },
        { name: "max_items", selector: { number: { min: 3, max: 50, mode: "box" } } },
        { name: "theme", selector: { select: { mode: "dropdown", options: [
          { value: "v2", label: "Bleu nuit (style des cartes MyElectricalData)" },
          { value: "auto", label: "Bleu nuit, clair si Home Assistant est en mode clair" },
          { value: "ha", label: "Thème de Home Assistant" }] } } },
        { name: "language", selector: { select: { mode: "dropdown", options: [
          { value: "auto", label: "Langue de Home Assistant" }, { value: "fr", label: "Français" },
          { value: "en", label: "English" }, { value: "pl", label: "Polski" }] } } },
      ],
      computeLabel: (s) => ({
        title: "Titre (Forum HACF par défaut)", show_latest: "Onglet Sujets", show_mine: "Onglet Mes sujets",
        show_notifications: "Onglet Notifications", show_avatars: "Avatars des membres", max_items: "Nombre de lignes affichées",
        theme: "Couleurs de la carte", language: "Langue",
      }[s.name] || s.name),
    };
  }

  setConfig(config) {
    this._config = { ...DEFAULTS, ...(config || {}) };
    this._sig = null;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    if (!this._clicks) {
      this.shadowRoot.addEventListener("click", (this._clicks = (ev) => {
        const tab = ev.target.closest?.("[data-tab]");
        if (tab) { this._tab = tab.dataset.tab; store.set("hacf-forum:tab", this._tab); this._sig = null; this._render(); return; }
        if (ev.target.closest?.("[data-act=seen]")) { this._markSeen(); this._sig = null; this._render(); }
      }));
    }
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  connectedCallback() {
    clearInterval(this._tick);
    this._tick = setInterval(() => { this._sig = null; this._render(); }, 60000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, rows: "auto", min_columns: 6 };
  }

  _t() {
    const want = this._config.language === "auto" ? String(this._hass?.locale?.language || this._hass?.language || "fr").slice(0, 2) : this._config.language;
    return I18N[want] || I18N.fr;
  }

  /** Capteurs de l'intégration (par leur clé de traduction). */
  _entities() {
    const reg = this._hass?.entities || {}, st = this._hass?.states || {};
    const out = {};
    for (const [id, e] of Object.entries(reg)) {
      if (e.platform !== "hacf_forum" || !st[id]) continue;
      if (e.translation_key === "latest_topics") out.latest ||= id;
      else if (e.translation_key === "my_topics") out.mine ||= id;
      else if (e.translation_key === "notifications") out.notifs ||= id;
    }
    return out;
  }

  _seenKey(kind) {
    return `hacf-forum:seen:${kind}`;
  }

  /** « Vu » : heure de la dernière visite (sujets), nombre de messages par sujet (mes sujets). */
  _markSeen() {
    const ents = this._entities();
    if (this._tab === "mine" && ents.mine) {
      const map = {};
      for (const t of this._hass.states[ents.mine].attributes?.topics || []) map[t.id] = t.highest_post;
      store.set(this._seenKey("mine"), map);
    } else {
      store.set(this._seenKey("latest"), Date.now());
    }
  }

  _ago(iso) {
    const d = iso ? new Date(iso) : null;
    if (!d || isNaN(d)) return "";
    const lang = this._t() === I18N.en ? "en" : this._t() === I18N.pl ? "pl" : "fr";
    const rtf = new Intl.RelativeTimeFormat(lang, { numeric: "auto" });
    const s = (d.getTime() - Date.now()) / 1000;
    const abs = Math.abs(s);
    if (abs < 60) return rtf.format(Math.round(s), "second");
    if (abs < 3600) return rtf.format(Math.round(s / 60), "minute");
    if (abs < 86400) return rtf.format(Math.round(s / 3600), "hour");
    if (abs < 86400 * 30) return rtf.format(Math.round(s / 86400), "day");
    return d.toLocaleDateString(lang, { day: "numeric", month: "short", year: "numeric" });
  }

  _themeClass() {
    const light = this._hass?.themes?.darkMode === false, th = this._config.theme;
    if (th === "ha") return `th-ha${light ? " light" : ""}`;
    if (th === "auto" && light) return "light";
    return "";
  }

  _topicRow(t, isNew, extra) {
    const T = this._t(), c = this._config;
    const avatar = c.show_avatars && safeImg(t.last_poster_avatar) ? `<img class="av" src="${esc(safeImg(t.last_poster_avatar))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<span class="av av-i"><ha-icon icon="mdi:account"></ha-icon></span>`;
    const flags = [t.pinned ? `<ha-icon icon="mdi:pin" title="${esc(T.pinned)}"></ha-icon>` : "", t.closed ? `<ha-icon icon="mdi:lock" title="${esc(T.closed)}"></ha-icon>` : "",
      t.solved ? `<ha-icon class="ok" icon="mdi:check-circle" title="${esc(T.solved)}"></ha-icon>` : ""].join("");
    const replies = Number(t.replies) || 0;
    return `<a class="row${isNew ? " new" : ""}" href="${esc(safeUrl(isNew ? t.last_url : t.url))}" target="_blank" rel="noopener noreferrer">
      ${avatar}
      <div class="rb">
        <div class="rt">${flags}<span>${esc(t.title)}</span>${isNew ? `<em>${esc(extra || T.new_badge)}</em>` : ""}</div>
        <div class="rm">${t.category ? `<span class="cat"><i style="background:${safeColor(t.category_color)}"></i>${esc(t.category)}</span>` : ""}
          <span><ha-icon icon="mdi:reply"></ha-icon>${replies}</span><span><ha-icon icon="mdi:eye-outline"></ha-icon>${Number(t.views) || 0}</span>
          ${t.likes ? `<span><ha-icon icon="mdi:heart-outline"></ha-icon>${Number(t.likes)}</span>` : ""}
          <span class="when">${esc(this._ago(t.last_posted_at))}${t.last_poster ? ` · ${esc(T.by)} ${esc(t.last_poster)}` : ""}</span></div>
      </div></a>`;
  }

  _notifRow(n) {
    const T = this._t();
    const label = (T.n[n.type] || T.n.other).replace("{u}", n.user || "").replace("{b}", n.badge || "").replace("{c}", n.count ?? "");
    return `<a class="row${n.read ? "" : " new"}" href="${esc(safeUrl(n.url))}" target="_blank" rel="noopener noreferrer">
      <span class="av av-i n-${n.read ? "read" : "unread"}"><ha-icon icon="${esc(N_ICON[n.type] || N_ICON.other)}"></ha-icon></span>
      <div class="rb"><div class="rt"><span>${esc(label)}</span></div>
        <div class="rm">${n.title ? `<span class="nt">${esc(n.title)}</span>` : ""}<span class="when">${esc(this._ago(n.created_at))}</span></div></div></a>`;
  }

  _render() {
    if (!this._config || !this._hass || !this.shadowRoot) return;
    const c = this._config, T = this._t();
    const ents = this._entities();
    const st = (id) => (id ? this._hass.states[id] : undefined);
    const sig = [c.theme, this._hass.themes?.darkMode, this._tab, Math.floor(Date.now() / 60000), ...Object.values(ents).map((id) => st(id)?.last_updated)].join("|");
    if (sig === this._sig) return;
    this._sig = sig;

    if (!ents.latest) {
      this._card(`<div class="empty"><b>${esc(T.missing)}</b><span>${esc(T.missing_hint)}</span></div>`, T.title, "");
      return;
    }
    const latest = st(ents.latest).attributes || {};
    const mine = st(ents.mine)?.attributes || null;
    const notifs = st(ents.notifs)?.attributes || null;
    const max = Math.max(3, Number(c.max_items) || 10);

    // nouveautés depuis la dernière visite (première visite : tout est considéré comme vu)
    let seenAt = store.get(this._seenKey("latest"), 0);
    if (!seenAt) { seenAt = Date.now(); store.set(this._seenKey("latest"), seenAt); }
    const latestTopics = latest.topics || [];
    const isNewLatest = (t) => new Date(t.last_posted_at).getTime() > seenAt && !t.pinned;
    const newLatest = latestTopics.filter(isNewLatest).length;
    let seenMine = store.get(this._seenKey("mine"), null);
    const mineTopics = mine?.topics || [];
    if (!seenMine && mineTopics.length) { seenMine = Object.fromEntries(mineTopics.map((t) => [t.id, t.highest_post])); store.set(this._seenKey("mine"), seenMine); }
    const newReplies = (t) => (seenMine && seenMine[t.id] !== undefined ? Math.max(0, (t.highest_post || 0) - seenMine[t.id]) : 0);
    const newMine = mineTopics.reduce((a, t) => a + newReplies(t), 0);
    const unread = Number(st(ents.notifs)?.state) || 0;

    const tabs = [];
    if (c.show_latest !== false) tabs.push(["latest", "mdi:forum", T.latest, newLatest]);
    if (c.show_mine !== false && mine) tabs.push(["mine", "mdi:account-voice", T.mine, newMine]);
    if (c.show_notifications !== false) tabs.push(["notifs", unread ? "mdi:bell-badge" : "mdi:bell", T.notifs, unread]);
    if (!this._tab) this._tab = store.get("hacf-forum:tab", "latest");
    if (!tabs.some(([k]) => k === this._tab)) this._tab = tabs[0]?.[0] || "latest";

    let body = "", link = latest.forum_url, canSee = false;
    if (this._tab === "latest") {
      const rows = latestTopics.slice(0, max).map((t) => this._topicRow(t, isNewLatest(t)));
      body = rows.length ? rows.join("") : `<div class="none">${esc(T.none_latest)}</div>`;
      canSee = true;
    } else if (this._tab === "mine") {
      link = mine.forum_url;
      const rows = mineTopics.slice(0, max).map((t) => { const n = newReplies(t); return this._topicRow(t, n > 0, `+${n}`); });
      body = rows.length ? rows.join("") : `<div class="none">${esc(T.none_mine)}</div>`;
      canSee = true;
    } else {
      if (!notifs) body = `<div class="none">${esc(T.no_account)}</div>`;
      else {
        link = notifs.forum_url;
        const rows = (notifs.notifications || []).slice(0, max).map((n) => this._notifRow(n));
        body = rows.length ? rows.join("") : `<div class="none">${esc(T.none_notifs)}</div>`;
      }
    }

    const tabBar = tabs.length > 1 ? `<div class="tabs" role="tablist">${tabs.map(([k, icon, label, n]) =>
      `<button class="tab${k === this._tab ? " on" : ""}" role="tab" aria-selected="${k === this._tab}" data-tab="${k}"><ha-icon icon="${icon}"></ha-icon>${esc(label)}${n ? `<b>${n}</b>` : ""}</button>`).join("")}</div>` : "";
    const sub = latest.category?.full_name || T.all;
    const updated = st(ents.latest)?.last_updated;
    const foot = `<div class="foot">${canSee ? `<button class="seen" data-act="seen"><ha-icon icon="mdi:check-all"></ha-icon>${esc(T.seen)}</button>` : "<span></span>"}
      <span>${esc(T.updated)} ${esc(this._ago(updated))} · ${esc(T.unofficial)}</span></div>`;
    this._card(tabBar + `<div class="list">${body}</div>` + foot, c.title || T.title, sub, safeUrl(link));
  }

  _card(body, title, sub, link = FORUM) {
    const T = this._t();
    this.shadowRoot.innerHTML = `${STYLE}<ha-card class="${this._themeClass()}">
      <header><div class="brand"><span class="logo"><ha-icon icon="mdi:forum"></ha-icon></span>
        <div><div class="title">${esc(title)}</div>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div></div>
        <a class="go" href="${esc(link)}" target="_blank" rel="noopener noreferrer" title="${esc(T.open)}" aria-label="${esc(T.open)}"><ha-icon icon="mdi:open-in-new"></ha-icon></a></header>
      ${body}</ha-card>`;
  }
}

const STYLE = `<style>
:host {
  --f-bg: #1a2434; --f-surface: #212d40; --f-line: #2f3d55; --f-text: #e7edf5; --f-muted: #8fa0b8;
  --f-accent: #1d93e3; --f-green: #96d21f; --f-new: #f0a33a; --f-on-accent: #fff;
}
ha-card { background: var(--f-bg); color: var(--f-text); border: 1px solid var(--f-line); border-radius: 18px; overflow: hidden; }
ha-card.light { --f-bg: #f4f6fa; --f-surface: #e8edf4; --f-line: #d3dbe6; --f-text: #1a2434; --f-muted: #5b6b82; --f-accent: #1673b8; --f-green: #4c8a0b; --f-new: #b35619; }
ha-card.th-ha { --f-bg: var(--ha-card-background, var(--card-background-color)); --f-surface: color-mix(in srgb, var(--primary-text-color, #000) 6%, transparent);
  --f-line: var(--divider-color, rgba(127,127,127,.25)); --f-text: var(--primary-text-color); --f-muted: var(--secondary-text-color);
  --f-accent: var(--primary-color, #1d93e3); --f-on-accent: var(--text-primary-color, #fff); border-radius: var(--ha-card-border-radius, 12px); }
header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px 8px; }
.brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
.logo { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 10px; background: color-mix(in srgb, var(--f-accent) 18%, transparent); flex: none; }
.logo ha-icon { --mdc-icon-size: 22px; color: var(--f-accent); }
.title { font-size: 1.1rem; font-weight: 700; }
.sub { font-size: .76rem; color: var(--f-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.go { color: var(--f-muted); display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; }
.go:hover, .go:focus-visible { color: var(--f-accent); background: var(--f-surface); outline: none; }
.tabs { display: flex; gap: 6px; padding: 4px 12px 8px; flex-wrap: wrap; }
.tab { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--f-line);
  background: var(--f-surface); color: var(--f-text); font: inherit; font-size: .82rem; cursor: pointer; }
.tab ha-icon { --mdc-icon-size: 16px; color: var(--f-muted); }
.tab.on { background: var(--f-accent); border-color: var(--f-accent); color: var(--f-on-accent); }
.tab.on ha-icon { color: var(--f-on-accent); }
.tab b { min-width: 18px; padding: 0 5px; border-radius: 9px; background: var(--f-new); color: #1a2434; font-size: .7rem; line-height: 18px; text-align: center; }
.tab:focus-visible, .seen:focus-visible, .row:focus-visible { outline: 2px solid var(--f-accent); outline-offset: 2px; }
.list { display: flex; flex-direction: column; gap: 6px; padding: 0 12px; }
.row { display: flex; gap: 10px; align-items: flex-start; padding: 9px 10px; border-radius: 12px; background: var(--f-surface);
  border: 1px solid transparent; color: inherit; text-decoration: none; min-width: 0; }
.row:hover { border-color: var(--f-line); }
.row.new { border-color: color-mix(in srgb, var(--f-new) 55%, var(--f-line)); }
.av { width: 32px; height: 32px; border-radius: 50%; flex: none; object-fit: cover; background: var(--f-line); }
.av-i { display: grid; place-items: center; }
.av-i ha-icon { --mdc-icon-size: 18px; color: var(--f-muted); }
.av-i.n-unread { background: color-mix(in srgb, var(--f-accent) 22%, transparent); }
.av-i.n-unread ha-icon { color: var(--f-accent); }
.rb { min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 3px; }
.rt { display: flex; align-items: center; gap: 5px; font-size: .88rem; font-weight: 600; line-height: 1.3; min-width: 0; }
.rt span { overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.rt ha-icon { --mdc-icon-size: 15px; color: var(--f-muted); flex: none; }
.rt ha-icon.ok { color: var(--f-green); }
.rt em { font-style: normal; font-size: .68rem; font-weight: 700; color: #1a2434; background: var(--f-new); padding: 0 6px; border-radius: 8px; flex: none; }
.rm { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; font-size: .74rem; color: var(--f-muted); }
.rm span { display: inline-flex; align-items: center; gap: 3px; }
.rm ha-icon { --mdc-icon-size: 13px; }
.cat i { width: 8px; height: 8px; border-radius: 2px; flex: none; }
.nt { color: var(--f-text); opacity: .85; }
.when { white-space: nowrap; }
.none, .empty { padding: 14px 4px; font-size: .86rem; color: var(--f-muted); }
.empty { display: flex; flex-direction: column; gap: 6px; padding: 4px 16px 16px; }
.empty b { color: var(--f-text); }
.foot { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; padding: 10px 14px 12px; font-size: .72rem; color: var(--f-muted); }
.seen { display: inline-flex; align-items: center; gap: 4px; background: none; border: 1px solid var(--f-line); color: var(--f-text);
  border-radius: 999px; padding: 4px 10px; font: inherit; font-size: .74rem; cursor: pointer; }
.seen ha-icon { --mdc-icon-size: 15px; color: var(--f-accent); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>`;

if (!customElements.get("hacf-forum-card")) customElements.define("hacf-forum-card", HacfForumCard);
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "hacf-forum-card")) {
  window.customCards.push({
    type: "hacf-forum-card",
    name: "Forum HACF",
    description: "Derniers sujets, vos sujets et vos notifications du forum HACF (intégration non officielle).",
    preview: true,
    documentationURL: "https://github.com/Marlboro62/hacf-forum",
  });
}
console.info(`%c HACF-FORUM-CARD %c ${CARD_VERSION} `, "background:#96d21f;color:#1a2434;font-weight:700", "background:#1d93e3;color:#fff");
})();
