/*
 * Carte Forum HACF — custom:hacf-forum-card
 *
 * Affiche les capteurs de l'intégration HACF Forum (non officielle) : derniers sujets du forum de la
 * communauté francophone de Home Assistant, sujets du membre et notifications du compte relié.
 * Chargée automatiquement par l'intégration : aucune ressource à ajouter.
 *
 * © 2026 Marlboro62. Tous droits réservés : copie, diffusion et modification interdites sans accord écrit (voir LICENSE).
 */
(() => {
const CARD_VERSION = "0.4.0b2";
const FORUM = "https://forum.hacf.fr";
const SITE = "https://www.hacf.fr";

const DEFAULTS = {
  title: "",
  show_latest: true,
  show_mine: true,
  show_notifications: true,
  show_news: true,
  // onglets des fonctions facultatives : affichés quand leur interrupteur est activé dans l'intégration
  show_popular: true,
  show_unanswered: true,
  show_search: true,
  show_posts: true,
  show_unread: true,
  show_tracked: true,
  show_bookmarks: true,
  show_messages: true,
  max_items: 10,
  scroll: true,
  show_avatars: true,
  theme: "v2",
  language: "auto",
};

/* Capteurs des fonctions facultatives (clé de traduction → onglet) */
const LIST_KEYS = {
  popular_topics: "popular", unanswered_topics: "unanswered", search_results: "search", latest_posts: "posts",
  unread_topics: "unread", new_topics: "fresh", tracked_topics: "tracked", bookmarks: "bookmarks", private_messages: "pms",
};

/* ---------------------------------------------------------------- textes */

const I18N = {
  fr: {
    title: "Forum HACF", all: "Tout le forum", latest: "Sujets", mine: "Mes sujets", notifs: "Notifications",
    open: "Ouvrir le forum", refresh: "Actualiser maintenant", seen: "Tout marquer comme vu", below: "{n} nouveau(x) plus bas", none_latest: "Aucun sujet pour le moment.",
    none_mine: "Aucun sujet ouvert par ce pseudo.", none_notifs: "Aucune notification.", unread: "non lues",
    news: "nouveaux", new_badge: "nouveau", replies: "réponses", reply: "réponse", views: "vues", likes: "j'aime",
    by: "dernier message de", updated: "Mis à jour", unofficial: "Intégration non officielle",
    missing: "Intégration HACF Forum introuvable", missing_hint: "Ajoutez-la dans Paramètres › Appareils et services › Ajouter une intégration › HACF Forum.",
    no_account: "Reliez votre compte HACF pour voir vos notifications : Paramètres › Appareils et services › HACF Forum › Configurer.",
    pinned: "Épinglé", closed: "Fermé", solved: "Résolu",
    actus: "Actus", news_sub: "Actualités de hacf.fr", none_news: "Aucune actualité pour le moment.", author: "par",
    popular: "Populaires", unanswered: "Sans réponse", search: "Recherche", posts: "Messages", unread_tab: "Non lus", tracked: "Suivis",
    bookmarks: "Signets", pms: "Privés", none_list: "Rien pour le moment.", reminder: "rappel", period: { daily: "du jour", weekly: "de la semaine", monthly: "du mois", yearly: "de l'année" },
    popular_sub: "Sujets populaires {p}", unanswered_sub: "Sujets sans réponse", search_sub: "Recherche : {q}", posts_sub: "Derniers messages",
    unread_sub: "Non lus et nouveaux", tracked_sub: "Sujets suivis", bookmarks_sub: "Mes signets", pms_sub: "Messages privés",
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
    open: "Open the forum", refresh: "Refresh now", seen: "Mark all as seen", below: "{n} new below", none_latest: "No topics yet.",
    none_mine: "No topics opened by this user.", none_notifs: "No notifications.", unread: "unread",
    news: "new", new_badge: "new", replies: "replies", reply: "reply", views: "views", likes: "likes",
    by: "last post by", updated: "Updated", unofficial: "Unofficial integration",
    missing: "HACF Forum integration not found", missing_hint: "Add it in Settings › Devices & services › Add integration › HACF Forum.",
    no_account: "Link your HACF account to see your notifications: Settings › Devices & services › HACF Forum › Configure.",
    pinned: "Pinned", closed: "Closed", solved: "Solved",
    actus: "News", news_sub: "hacf.fr news", none_news: "No news yet.", author: "by",
    popular: "Popular", unanswered: "Unanswered", search: "Search", posts: "Posts", unread_tab: "Unread", tracked: "Tracked",
    bookmarks: "Bookmarks", pms: "Messages", none_list: "Nothing yet.", reminder: "reminder", period: { daily: "today", weekly: "this week", monthly: "this month", yearly: "this year" },
    popular_sub: "Popular topics {p}", unanswered_sub: "Unanswered topics", search_sub: "Search: {q}", posts_sub: "Latest posts",
    unread_sub: "Unread and new", tracked_sub: "Tracked topics", bookmarks_sub: "My bookmarks", pms_sub: "Private messages",
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
    open: "Otwórz forum", refresh: "Odśwież teraz", seen: "Oznacz wszystko jako przejrzane", below: "{n} nowe poniżej", none_latest: "Brak tematów.",
    none_mine: "Brak tematów tego użytkownika.", none_notifs: "Brak powiadomień.", unread: "nieprzeczytane",
    news: "nowe", new_badge: "nowe", replies: "odpowiedzi", reply: "odpowiedź", views: "wyświetleń", likes: "polubień",
    by: "ostatni post:", updated: "Zaktualizowano", unofficial: "Integracja nieoficjalna",
    missing: "Nie znaleziono integracji HACF Forum", missing_hint: "Dodaj ją w Ustawienia › Urządzenia i usługi › Dodaj integrację › HACF Forum.",
    no_account: "Połącz konto HACF, aby widzieć powiadomienia: Ustawienia › Urządzenia i usługi › HACF Forum › Konfiguruj.",
    pinned: "Przypięty", closed: "Zamknięty", solved: "Rozwiązany",
    actus: "Aktualności", news_sub: "Aktualności hacf.fr", none_news: "Brak aktualności.", author: "autor:",
    popular: "Popularne", unanswered: "Bez odpowiedzi", search: "Szukaj", posts: "Posty", unread_tab: "Nieprzeczytane", tracked: "Śledzone",
    bookmarks: "Zakładki", pms: "Prywatne", none_list: "Na razie nic.", reminder: "przypomnienie", period: { daily: "dnia", weekly: "tygodnia", monthly: "miesiąca", yearly: "roku" },
    popular_sub: "Popularne tematy {p}", unanswered_sub: "Tematy bez odpowiedzi", search_sub: "Szukaj: {q}", posts_sub: "Najnowsze posty",
    unread_sub: "Nieprzeczytane i nowe", tracked_sub: "Śledzone tematy", bookmarks_sub: "Moje zakładki", pms_sub: "Wiadomości prywatne",
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
// liens : seulement vers le forum ou le site hacf.fr (on ne fait confiance qu'à leurs adresses)
const safeUrl = (u) => (typeof u === "string" && (u.startsWith(FORUM + "/") || u.startsWith(SITE + "/")) ? u : FORUM);
const safeColor = (c) => (/^#[0-9a-f]{3,8}$/i.test(String(c || "")) ? c : "#8fa0b8");
const safeImg = (u) => (typeof u === "string" && /^https:\/\/[^\s"'<>]+$/.test(u) ? u : "");

const store = {
  get(k, d) { try { const v = JSON.parse(window.localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } },
  set(k, v) { try { window.localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* stockage indisponible */ } },
};

/** « Vu » partagé entre les appareils : données utilisateur de Home Assistant (frontend/*_user_data),
 *  propres à chaque compte HA ; le stockage local du navigateur sert de cache et de secours. */
const SEEN_KINDS = ["latest", "mine", "news"];
const SEEN_KEY = "hacf_forum_seen";
const seenSync = {
  conn: null,
  cards: new Set(),
  start(hass) {
    const conn = hass?.connection;
    if (!conn || conn === this.conn) return;
    this.conn = conn;
    const apply = (value) => {
      if (!value || typeof value !== "object") return;
      // la version la plus récente gagne : un « vu » fait ici, pas encore envoyé, n'est pas écrasé
      if ((Number(value.at) || 0) < store.get("hacf-forum:seen:at", 0)) return;
      for (const k of SEEN_KINDS) if (value[k] != null) store.set(`hacf-forum:seen:${k}`, value[k]);
      store.set("hacf-forum:seen:at", Number(value.at) || 0);
      for (const card of this.cards) { card._sig = null; card._render(); }
    };
    // lecture au démarrage, puis mises à jour en direct quand un autre appareil marque comme vu
    hass.callWS({ type: "frontend/get_user_data", key: SEEN_KEY }).then((r) => apply(r?.value)).catch(() => {});
    conn.subscribeMessage((msg) => apply(msg?.value), { type: "frontend/subscribe_user_data", key: SEEN_KEY }).catch(() => {});
  },
  push(hass) {
    const value = { at: Date.now() };
    for (const k of SEEN_KINDS) value[k] = store.get(`hacf-forum:seen:${k}`, null);
    store.set("hacf-forum:seen:at", value.at);
    hass?.callWS({ type: "frontend/set_user_data", key: SEEN_KEY, value }).catch(() => { /* HA trop ancien : reste local */ });
  },
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
          { name: "show_news", selector: { boolean: {} } },
          { name: "show_popular", selector: { boolean: {} } },
          { name: "show_unanswered", selector: { boolean: {} } },
          { name: "show_search", selector: { boolean: {} } },
          { name: "show_posts", selector: { boolean: {} } },
          { name: "show_unread", selector: { boolean: {} } },
          { name: "show_tracked", selector: { boolean: {} } },
          { name: "show_bookmarks", selector: { boolean: {} } },
          { name: "show_messages", selector: { boolean: {} } },
          { name: "show_avatars", selector: { boolean: {} } },
        ] },
        { name: "max_items", selector: { number: { min: 3, max: 50, mode: "box" } } },
        { name: "scroll", selector: { boolean: {} } },
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
        show_notifications: "Onglet Notifications", show_news: "Onglet Actus (hacf.fr)",
        show_popular: "Onglet Populaires", show_unanswered: "Onglet Sans réponse", show_search: "Onglet Recherche", show_posts: "Onglet Messages",
        show_unread: "Onglet Non lus", show_tracked: "Onglet Suivis", show_bookmarks: "Onglet Signets", show_messages: "Onglet Messages privés", show_avatars: "Avatars des membres", max_items: "Nombre de lignes affichées",
        scroll: "Faire défiler la liste pour voir tous les sujets au-delà de ces lignes",
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
        if (ev.target.closest?.("[data-act=refresh]")) this._refresh();
        if (ev.target.closest?.("[data-act=below]")) {
          const list = this.shadowRoot.querySelector(".list.scroll");
          const first = list && [...list.querySelectorAll(".row.new")].find((r) => r.offsetTop >= list.scrollTop + list.clientHeight - 4);
          if (first) list.scrollTo({ top: first.offsetTop - 4, behavior: "smooth" });
        }
      }));
    }
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    seenSync.start(hass);
    this._render();
  }

  connectedCallback() {
    seenSync.cards.add(this);
    clearInterval(this._tick);
    this._tick = setInterval(() => { this._sig = null; this._render(); }, 60000);
    // carte rattachée à la page (changement de vue) : refaire la mesure de la liste
    if (this._hass) { this._sig = null; this._render(); }
  }

  disconnectedCallback() {
    seenSync.cards.delete(this);
    clearInterval(this._tick);
    this._fitObs?.disconnect();
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
      else if (e.translation_key === "news") out.news ||= id;
      else if (e.translation_key === "refresh" && id.startsWith("button.")) out.refresh ||= id;
      else if (LIST_KEYS[e.translation_key]) out[LIST_KEYS[e.translation_key]] ||= id;
    }
    return out;
  }

  /** Actualiser : bouton de l'intégration (tout est relu), sinon mise à jour du capteur des derniers sujets. */
  _refresh() {
    const ents = this._entities();
    if (this._busy || !ents.latest) return;
    const before = this._hass.states[ents.latest]?.last_updated;
    const call = ents.refresh ? this._hass.callService("button", "press", { entity_id: ents.refresh })
      : this._hass.callService("homeassistant", "update_entity", { entity_id: ents.latest });
    this._busy = { before, until: Date.now() + 20000 };
    this._sig = null; this._render();
    const done = () => { this._busy = null; this._sig = null; this._render(); };
    // l'appel se termine une fois le forum relu (ou le capteur mis à jour) : fin de l'animation
    Promise.resolve(call).then(done, done);
    clearTimeout(this._busyTimer);
    this._busyTimer = setTimeout(done, 20000);
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
    } else if (this._tab === "news") {
      store.set(this._seenKey("news"), Date.now());
    } else {
      store.set(this._seenKey("latest"), Date.now());
    }
    seenSync.push(this._hass);  // les autres appareils du même compte HA le reçoivent aussitôt
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
        ${t.excerpt ? `<div class="sum">${esc(t.excerpt)}</div>` : ""}
        <div class="rm">${t.category ? `<span class="cat"><i style="background:${safeColor(t.category_color)}"></i>${esc(t.category)}</span>` : ""}
          <span><ha-icon icon="mdi:reply"></ha-icon>${replies}</span><span><ha-icon icon="mdi:eye-outline"></ha-icon>${Number(t.views) || 0}</span>
          ${t.likes ? `<span><ha-icon icon="mdi:heart-outline"></ha-icon>${Number(t.likes)}</span>` : ""}
          <span class="when">${esc(this._ago(t.last_posted_at))}${t.last_poster ? ` · ${esc(T.by)} ${esc(t.last_poster)}` : ""}</span></div>
      </div></a>`;
  }

  _newsRow(a, isNew) {
    const T = this._t();
    const img = safeImg(a.image);
    const thumb = img ? `<img class="th" src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
      : `<span class="th th-i"><ha-icon icon="mdi:newspaper-variant-outline"></ha-icon></span>`;
    return `<a class="row${isNew ? " new" : ""}" href="${esc(safeUrl(a.url))}" target="_blank" rel="noopener noreferrer">
      ${thumb}
      <div class="rb">
        <div class="rt"><span>${esc(a.title)}</span>${isNew ? `<em>${esc(T.new_badge)}</em>` : ""}</div>
        ${a.summary ? `<div class="sum">${esc(a.summary)}</div>` : ""}
        <div class="rm"><span class="when">${esc(this._ago(a.published_at))}${a.author ? ` · ${esc(T.author)} ${esc(a.author)}` : ""}</span></div>
      </div></a>`;
  }

  _postRow(p) {
    const T = this._t(), c = this._config;
    const avatar = c.show_avatars && safeImg(p.avatar) ? `<img class="av" src="${esc(safeImg(p.avatar))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<span class="av av-i"><ha-icon icon="mdi:account"></ha-icon></span>`;
    return `<a class="row" href="${esc(safeUrl(p.url))}" target="_blank" rel="noopener noreferrer">
      ${avatar}
      <div class="rb"><div class="rt"><span>${esc(p.title)}</span></div>
        ${p.excerpt ? `<div class="sum">${esc(p.excerpt)}</div>` : ""}
        <div class="rm">${p.category ? `<span class="cat"><i style="background:${safeColor(p.category_color)}"></i>${esc(p.category)}</span>` : ""}
          <span class="when">${esc(this._ago(p.created_at))}${p.user ? ` · ${esc(T.author)} ${esc(p.user)}` : ""}</span></div></div></a>`;
  }

  _bookmarkRow(b) {
    const T = this._t();
    const remind = b.reminder_at && new Date(b.reminder_at).getTime() > Date.now();
    return `<a class="row${remind ? " new" : ""}" href="${esc(safeUrl(b.url))}" target="_blank" rel="noopener noreferrer">
      <span class="av av-i"><ha-icon icon="${remind ? "mdi:bookmark-clock" : "mdi:bookmark"}"></ha-icon></span>
      <div class="rb"><div class="rt"><span>${esc(b.name || b.title)}</span></div>
        ${b.name && b.title ? `<div class="sum">${esc(b.title)}</div>` : b.excerpt ? `<div class="sum">${esc(b.excerpt)}</div>` : ""}
        <div class="rm"><span class="when">${esc(this._ago(b.created_at))}${remind ? ` · ${esc(T.reminder)} ${esc(this._ago(b.reminder_at))}` : ""}</span></div></div></a>`;
  }

  _notifRow(n) {
    const T = this._t();
    const label = (T.n[n.type] || T.n.other).replace("{u}", n.user || "").replace("{b}", n.badge || "").replace("{c}", n.count ?? "");
    return `<a class="row${n.read ? "" : " new"}" href="${esc(safeUrl(n.url))}" target="_blank" rel="noopener noreferrer">
      <span class="av av-i n-${n.read ? "read" : "unread"}"><ha-icon icon="${esc(N_ICON[n.type] || N_ICON.other)}"></ha-icon></span>
      <div class="rb"><div class="rt"><span>${esc(label)}</span></div>
        <div class="rm">${n.title && !(n.type === "granted_badge" && n.title === n.badge) ? `<span class="nt">${esc(n.title)}</span>` : ""}<span class="when">${esc(this._ago(n.created_at))}</span></div></div></a>`;
  }

  _render() {
    if (!this._config || !this._hass || !this.shadowRoot) return;
    const c = this._config, T = this._t();
    const ents = this._entities();
    const st = (id) => (id ? this._hass.states[id] : undefined);
    if (this._busy && st(ents.latest)?.last_updated !== this._busy.before) { this._busy = null; clearTimeout(this._busyTimer); }
    const sig = [!!this._busy, c.theme, this._hass.themes?.darkMode, this._tab, Math.floor(Date.now() / 60000), ...Object.values(ents).map((id) => st(id)?.last_updated)].join("|");
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
    // défilement : toutes les lignes sont présentes, la liste garde la hauteur de « max » lignes
    const scroll = c.scroll !== false;
    const cut = scroll ? Infinity : max;
    let hidden = 0;

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
    const news = st(ents.news)?.attributes || null;
    const articles = news?.articles || [];
    let seenNews = store.get(this._seenKey("news"), 0);
    if (!seenNews && articles.length) { seenNews = Date.now(); store.set(this._seenKey("news"), seenNews); }
    const isNewArticle = (a) => new Date(a.published_at).getTime() > seenNews;
    const newNews = articles.filter(isNewArticle).length;

    const tabs = [];
    if (c.show_latest !== false) tabs.push(["latest", "mdi:forum", T.latest, newLatest]);
    if (c.show_mine !== false && mine) tabs.push(["mine", "mdi:account-voice", T.mine, newMine]);
    if (c.show_notifications !== false) tabs.push(["notifs", unread ? "mdi:bell-badge" : "mdi:bell", T.notifs, unread]);
    if (c.show_news !== false && news) tabs.push(["news", "mdi:newspaper-variant-outline", T.actus, newNews]);
    // fonctions facultatives : un onglet par capteur présent
    const attrs = (k) => st(ents[k])?.attributes || null;
    const unreadList = [...(attrs("unread")?.topics || []), ...(attrs("fresh")?.topics || []).filter((t) => !(attrs("unread")?.topics || []).some((u) => u.id === t.id))];
    const extraTabs = [
      ["popular", "show_popular", "mdi:fire", T.popular, 0],
      ["unanswered", "show_unanswered", "mdi:help-circle-outline", T.unanswered, 0],
      ["search", "show_search", "mdi:magnify", T.search, 0],
      ["posts", "show_posts", "mdi:message-reply-text-outline", T.posts, 0],
      ["unread", "show_unread", "mdi:email-mark-as-unread", T.unread_tab, unreadList.length],
      ["tracked", "show_tracked", "mdi:eye-outline", T.tracked, 0],
      ["bookmarks", "show_bookmarks", "mdi:bookmark-outline", T.bookmarks, 0],
      ["pms", "show_messages", "mdi:email-outline", T.pms, Number(st(ents.pms)?.state) || 0],
    ];
    for (const [k, opt, icon, label, n] of extraTabs) {
      if (c[opt] !== false && (ents[k] || (k === "unread" && ents.fresh))) tabs.push([k, icon, label, n]);
    }
    if (!this._tab) this._tab = store.get("hacf-forum:tab", "latest");
    if (!tabs.some(([k]) => k === this._tab)) this._tab = tabs[0]?.[0] || "latest";

    // sous-titre : catégorie et/ou étiquette suivies (« Partages › Lovelace · #ia »), sinon tout le forum
    const followed = [latest.category?.full_name, latest.tag ? `#${latest.tag}` : ""].filter(Boolean).join(" · ");
    let body = "", link = latest.forum_url, canSee = false, sub = followed || T.all;
    if (this._tab === "latest") {
      const rows = latestTopics.slice(0, cut).map((t) => this._topicRow(t, isNewLatest(t)));
      hidden = latestTopics.slice(max).filter(isNewLatest).length;
      body = rows.length ? rows.join("") : `<div class="none">${esc(T.none_latest)}</div>`;
      canSee = true;
    } else if (this._tab === "mine") {
      link = mine.forum_url;
      const rows = mineTopics.slice(0, cut).map((t) => { const n = newReplies(t); return this._topicRow(t, n > 0, `+${n}`); });
      hidden = mineTopics.slice(max).filter((t) => newReplies(t) > 0).length;
      body = rows.length ? rows.join("") : `<div class="none">${esc(T.none_mine)}</div>`;
      canSee = true;
    } else if (this._tab === "news") {
      link = news.news_url;
      sub = T.news_sub;
      const rows = articles.slice(0, cut).map((a) => this._newsRow(a, isNewArticle(a)));
      hidden = articles.slice(max).filter(isNewArticle).length;
      body = rows.length ? rows.join("") : `<div class="none">${esc(T.none_news)}</div>`;
      canSee = true;
    } else if (this._tab !== "notifs") {
      // onglets des fonctions facultatives
      const a = attrs(this._tab === "unread" && !ents.unread ? "fresh" : this._tab) || {};
      const none = `<div class="none">${esc(T.none_list)}</div>`;
      link = a.forum_url || link;
      let items = a.topics || [];
      let row = (t) => this._topicRow(t, false);
      if (this._tab === "popular") sub = T.popular_sub.replace("{p}", T.period[a.popular_period] || "");
      else if (this._tab === "unanswered") sub = [T.unanswered_sub, followed].filter(Boolean).join(" · ");
      else if (this._tab === "search") sub = T.search_sub.replace("{q}", a.search_query || "");
      else if (this._tab === "posts") { sub = T.posts_sub; items = a.posts || []; row = (p) => this._postRow(p); }
      else if (this._tab === "unread") { sub = T.unread_sub; items = unreadList; row = (t) => this._topicRow(t, true, t.unread ? `+${t.unread}` : T.new_badge); }
      else if (this._tab === "tracked") { sub = T.tracked_sub; row = (t) => this._topicRow(t, t.unread > 0, `+${t.unread}`); }
      else if (this._tab === "bookmarks") { sub = T.bookmarks_sub; items = a.bookmarks || []; row = (b) => this._bookmarkRow(b); }
      else if (this._tab === "pms") { sub = T.pms_sub; row = (t) => this._topicRow(t, t.unread > 0, `+${t.unread}`); }
      const rows = items.slice(0, cut).map(row);
      body = rows.length ? rows.join("") : none;
    } else {
      if (!notifs) body = `<div class="none">${esc(T.no_account)}</div>`;
      else {
        link = notifs.forum_url;
        const all = notifs.notifications || [];
        const rows = all.slice(0, cut).map((n) => this._notifRow(n));
        hidden = all.slice(max).filter((n) => !n.read).length;
        body = rows.length ? rows.join("") : `<div class="none">${esc(T.none_notifs)}</div>`;
      }
    }

    const tabBar = tabs.length > 1 ? `<div class="tabs" role="tablist">${tabs.map(([k, icon, label, n]) =>
      `<button class="tab${k === this._tab ? " on" : ""}" role="tab" aria-selected="${k === this._tab}" data-tab="${k}"><ha-icon icon="${icon}"></ha-icon>${esc(label)}${n ? `<b>${n}</b>` : ""}</button>`).join("")}</div>` : "";
    const updated = st(ents.latest)?.last_updated;
    const below = scroll && hidden ? `<button class="below" data-act="below"><ha-icon icon="mdi:arrow-down"></ha-icon><span>${esc(T.below.replace("{n}", hidden))}</span></button>` : "";
    const foot = `<div class="foot"><span class="acts">${canSee ? `<button class="seen" data-act="seen"><ha-icon icon="mdi:check-all"></ha-icon>${esc(T.seen)}</button>` : ""}${below}</span>
      <span>${esc(T.updated)} ${esc(this._ago(updated))} · ${esc(T.unofficial)} · v${CARD_VERSION} © Marlboro62</span></div>`;
    this._card(tabBar + `<div class="list${scroll ? " scroll" : ""}" style="--f-rows:${max}">${body}</div>` + foot, c.title || T.title, sub, safeUrl(link));
    if (scroll) this._fitList(max);
  }

  /** Hauteur de la liste = ses « max » premières lignes ; les suivantes se voient en faisant défiler.
   *  La mesure n'est possible qu'une fois la carte affichée (onglet du tableau de bord ouvert, page chargée) :
   *  un ResizeObserver la refait dès que la carte prend sa taille, puis à chaque changement de largeur. */
  _fitList(max) {
    this._fitObs?.disconnect();
    const list = this.shadowRoot.querySelector(".list.scroll");
    if (!list) return;
    const btn = this.shadowRoot.querySelector(".below");
    const T = this._t();
    const fit = () => {
      const rows = list.querySelectorAll(":scope > .row");
      let want = "";
      if (rows.length) {
        const last = rows[Math.min(max, rows.length) - 1];
        const h = last.offsetTop + last.offsetHeight + 2;  // .list.scroll est positionnée : offsetTop relatif à la liste
        if (!(h > 2)) return;  // pas encore affichée : la mesure se fera plus tard
        // téléphone seulement (écran étroit ou peu haut) : les titres passent sur deux lignes, la liste ne dépasse pas
        // 60 % de l'écran pour que le bas de la carte (« Tout marquer comme vu ») reste accessible ;
        // tablette et ordinateur gardent leurs « max » lignes (en bas de la liste, le défilement passe à la page)
        const small = window.innerWidth < 600 || window.innerHeight < 500;
        const cap = small ? Math.max(240, Math.round(window.innerHeight * 0.6)) : Infinity;
        if (rows.length > max || h > cap) want = `${Math.min(h, cap)}px`;
      }
      if (list.style.maxHeight !== want) list.style.maxHeight = want;
      list.classList.add("fitted");
      count();
    };
    // bouton « n nouveaux plus bas » : recompté en faisant défiler, masqué quand tout a été vu
    const count = () => {
      if (!btn) return;
      const n = [...list.querySelectorAll(":scope > .row.new")].filter((r) => r.offsetTop >= list.scrollTop + list.clientHeight - 4).length;
      btn.hidden = n === 0;
      btn.lastChild.textContent = T.below.replace("{n}", n);
    };
    list.addEventListener("scroll", count, { passive: true });
    if (window.ResizeObserver) {
      this._fitObs = new ResizeObserver(() => fit());
      this._fitObs.observe(list);  // la liste passe de 0 à sa taille réelle quand la carte s'affiche
    }
    fit();
    requestAnimationFrame(fit);
  }

  _card(body, title, sub, link = FORUM) {
    const T = this._t();
    this.shadowRoot.innerHTML = `${STYLE}<ha-card class="${this._themeClass()}">
      <header><div class="brand"><span class="logo"><ha-icon icon="mdi:forum"></ha-icon></span>
        <div><div class="title">${esc(title)}</div>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div></div>
        <span class="hd-acts"><button class="go rf${this._busy ? " busy" : ""}" data-act="refresh" title="${esc(T.refresh)}" aria-label="${esc(T.refresh)}"${this._busy ? " disabled" : ""}><ha-icon icon="mdi:refresh"></ha-icon></button>
        <a class="go" href="${esc(link)}" target="_blank" rel="noopener noreferrer" title="${esc(T.open)}" aria-label="${esc(T.open)}"><ha-icon icon="mdi:open-in-new"></ha-icon></a></span></header>
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
.hd-acts { display: flex; align-items: center; gap: 2px; flex: none; }
button.go { border: 0; background: none; cursor: pointer; padding: 0; font: inherit; }
button.go.busy { cursor: progress; color: var(--f-accent); }
button.go.busy ha-icon { animation: f-spin 1s linear infinite; }
@keyframes f-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { button.go.busy ha-icon { animation: none; } }
.tabs { display: flex; gap: 6px; padding: 4px 12px 8px; flex-wrap: wrap; }
.tab { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--f-line);
  background: var(--f-surface); color: var(--f-text); font: inherit; font-size: .82rem; cursor: pointer; }
.tab ha-icon { --mdc-icon-size: 16px; color: var(--f-muted); }
.tab.on { background: var(--f-accent); border-color: var(--f-accent); color: var(--f-on-accent); }
.tab.on ha-icon { color: var(--f-on-accent); }
.tab b { min-width: 18px; padding: 0 5px; border-radius: 9px; background: var(--f-new); color: #1a2434; font-size: .7rem; line-height: 18px; text-align: center; }
.tab:focus-visible, .seen:focus-visible, .row:focus-visible { outline: 2px solid var(--f-accent); outline-offset: 2px; }
.list { display: flex; flex-direction: column; gap: 6px; padding: 0 12px; }
.list.scroll:not(.fitted) { max-height: calc(var(--f-rows, 10) * 60px); }
@media (max-width: 599px), (max-height: 499px) { .list.scroll:not(.fitted) { max-height: min(calc(var(--f-rows, 10) * 60px), 60vh); } }
.list.scroll { overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--f-line) transparent; position: relative; }
.acts { display: inline-flex; gap: 6px; flex-wrap: wrap; }
.below { display: inline-flex; align-items: center; gap: 4px; background: none; border: 1px solid var(--f-new); color: var(--f-new);
  border-radius: 999px; padding: 4px 10px; font: inherit; font-size: .72rem; cursor: pointer; }
.below ha-icon { --mdc-icon-size: 15px; }
.below[hidden] { display: none; }
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
.th { width: 76px; height: 46px; border-radius: 8px; flex: none; object-fit: cover; background: var(--f-line); }
.th-i { display: grid; place-items: center; }
.th-i ha-icon { --mdc-icon-size: 22px; color: var(--f-muted); }
.sum { font-size: .76rem; color: var(--f-text); opacity: .8; line-height: 1.35; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
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
    description: "Derniers sujets, vos sujets et vos notifications du forum HACF, et les actualités de hacf.fr (intégration non officielle).",
    preview: true,
    documentationURL: "https://github.com/Marlboro62/hacf-forum",
  });
}
console.info(`%c HACF-FORUM-CARD %c ${CARD_VERSION} © Marlboro62 `, "background:#96d21f;color:#1a2434;font-weight:700", "background:#1d93e3;color:#fff");
})();
