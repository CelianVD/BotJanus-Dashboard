# Structure :
#   1. GLASS_CSS   : <link> polices + script thème + feuille de style globale
#                    (nom conservé : les routes passent glass_css=GLASS_CSS)
#   2. Briques     : icônes SVG, barre d'onglets (NAV_FULL / NAV_BARE), JS commun
#                    (thème, toasts, sondage de statut) et _page() qui assemble
#   3. Pages       : une constante *_HTML par écran (mêmes noms qu'avant)
# Les variables Jinja et les noms d'endpoints sont inchangés.

# ------------------------------------------------------------
# 1. STYLE GLOBAL
# ------------------------------------------------------------
GLASS_CSS = r"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<script>
  /* Thème : mode "auto" (suit le système, en direct) par défaut, ou choix manuel clair/sombre.
     Clé bj_theme = 'light' | 'dark' ; absente = auto. */
  (function () {
    var root = document.documentElement, mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;
    function getMode() { var m = null; try { m = localStorage.getItem('bj_theme'); } catch (e) {} return (m === 'light' || m === 'dark') ? m : 'auto'; }
    window.bjApplyTheme = function () {
      var m = getMode();
      root.setAttribute('data-mode', m);
      root.setAttribute('data-theme', m !== 'auto' ? m : ((mq && mq.matches) ? 'light' : 'dark'));
    };
    window.bjSetMode = function (m) { try { if (m === 'auto') localStorage.removeItem('bj_theme'); else localStorage.setItem('bj_theme', m); } catch (e) {} window.bjApplyTheme(); };
    window.bjGetMode = getMode;
    window.bjApplyTheme();
    if (mq) { if (mq.addEventListener) mq.addEventListener('change', window.bjApplyTheme); else if (mq.addListener) mq.addListener(window.bjApplyTheme); }
  })();
</script>
<style>
    :root, :root[data-theme="dark"] {
        --bg-color: #08080a;
        --gradient-1: #4f46e5; --gradient-2: #7c3aed; --gradient-3: #2563eb;
        --card-bg: rgba(18, 18, 22, 0.65);
        --card-border: rgba(255, 255, 255, 0.12);
        --text-main: #ffffff; --text-muted: #a1a1aa;
        --btn-primary-bg: #ffffff; --btn-primary-text: #000000;
        --btn-secondary-border: #ffffff;
        --tag-bg: rgba(255, 255, 255, 0.05); --tag-border: rgba(255, 255, 255, 0.15);
        --input-bg: rgba(0, 0, 0, 0.35);
        --topbar-bg: rgba(255, 255, 255, 0.07); --topbar-border: rgba(255, 255, 255, 0.16);
        --toast-bg: rgba(20, 20, 26, 0.97);
        --console-bg: rgba(0, 0, 0, 0.72); --console-text: #4ade80;
        --row-hover: rgba(255, 255, 255, 0.04);
        --ok: #4ade80; --err: #f87171; --warn: #fbbf24; --info: #60a5fa;
        color-scheme: dark;
    }
    :root[data-theme="light"] {
        --bg-color: #f8fafc;
        --gradient-1: #38bdf8; --gradient-2: #818cf8; --gradient-3: #c084fc;
        --card-bg: rgba(255, 255, 255, 0.75);
        --card-border: rgba(0, 0, 0, 0.1);
        --text-main: #0f172a; --text-muted: #475569;
        --btn-primary-bg: #000000; --btn-primary-text: #ffffff;
        --btn-secondary-border: #000000;
        --tag-bg: rgba(0, 0, 0, 0.04); --tag-border: rgba(0, 0, 0, 0.12);
        --input-bg: rgba(255, 255, 255, 0.8);
        --topbar-bg: rgba(255, 255, 255, 0.55); --topbar-border: rgba(255, 255, 255, 0.9);
        --toast-bg: rgba(255, 255, 255, 0.98);
        --console-bg: rgba(15, 23, 42, 0.92); --console-text: #4ade80;
        --row-hover: rgba(0, 0, 0, 0.035);
        --ok: #16a34a; --err: #dc2626; --warn: #d97706; --info: #2563eb;
        color-scheme: light;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; }
    [hidden] { display: none !important; }

    body {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: var(--bg-color); color: var(--text-main);
        min-height: 100vh; position: relative; overflow-x: hidden;
        transition: background-color .4s ease, color .4s ease;
    }
    a { color: inherit; }

    /* ---------- Fond animé ---------- */
    .gradient-bg { position: fixed; inset: 0; z-index: 0; overflow: hidden; opacity: .55; pointer-events: none; contain: strict; }
    .blob { position: absolute; border-radius: 50%; will-change: transform; transform: translate3d(0,0,0); animation: float 22s ease-in-out infinite alternate; }
    .blob-1 { top: -25%; left: -20%; width: 75vw; height: 75vw; background: radial-gradient(circle, var(--gradient-1) 0%, transparent 65%); }
    .blob-2 { bottom: -35%; right: -25%; width: 90vw; height: 90vw; background: radial-gradient(circle, var(--gradient-2) 0%, transparent 65%); animation-delay: -7s; }
    .blob-3 { top: 20%; left: 20%; width: 65vw; height: 65vw; background: radial-gradient(circle, var(--gradient-3) 0%, transparent 65%); animation-delay: -14s; }
    @keyframes float { 0% { transform: translate3d(0,0,0) scale(1); } 50% { transform: translate3d(6vw,3vw,0) scale(1.08); } 100% { transform: translate3d(-3vw,6vw,0) scale(.94); } }
    @media (prefers-reduced-motion: reduce) { .blob { animation: none; } }

    /* ---------- Barre supérieure + onglets (pièce maîtresse) ---------- */
    .topbar {
        position: fixed; top: 0; left: 0; right: 0; z-index: 60;
        display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;
        padding: 12px 24px;
        background: var(--topbar-bg); border-bottom: 1px solid var(--topbar-border);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    }
    .brand { justify-self: start; display: inline-flex; align-items: center; gap: 12px; text-decoration: none;
             font-family: 'Syne', sans-serif; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; font-size: 1.05rem; }
    .brand img { width: 44px; height: 44px; object-fit: cover; border: 1px solid var(--card-border); display: block; }
    .tabbar {
        display: flex; align-items: stretch; height: 50px;
        background: var(--card-bg); border: 1px solid var(--card-border);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 12px 30px rgba(0,0,0,.14);
    }
    .tab {
        position: relative; display: inline-flex; align-items: center; justify-content: center; gap: 9px;
        padding: 0 20px; text-decoration: none; color: var(--text-muted);
        font-size: .74rem; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; white-space: nowrap;
        border-right: 1px solid var(--card-border); transition: background-color .2s, color .2s;
    }
    .tab:last-child { border-right: 0; }
    .tab svg { width: 17px; height: 17px; flex: none; }
    .tab:hover { color: var(--text-main); background: var(--row-hover); }
    .tab.active { background: var(--btn-primary-bg); color: var(--btn-primary-text); }
    .tab.exit { padding: 0 16px; }
    .tab.exit:hover { background: var(--err); color: #fff; }
    .tools { justify-self: end; display: flex; gap: 8px; }
    .icon-btn {
        width: 50px; height: 50px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer;
        background: var(--card-bg); border: 1px solid var(--card-border); color: var(--text-main);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: border-color .2s;
    }
    .icon-btn:hover { border-color: var(--text-main); }
    .icon-btn svg { width: 19px; height: 19px; }
    .icon-btn .i-sun, .icon-btn .i-moon, .icon-btn .i-auto { display: none; }
    :root[data-mode="light"] .icon-btn .i-sun, :root[data-mode="dark"] .icon-btn .i-moon, :root[data-mode="auto"] .icon-btn .i-auto { display: block; }

    .badge-dot {
        position: absolute; top: -8px; right: -6px; min-width: 17px; height: 17px; padding: 0 4px;
        background: var(--err); color: #fff; font-size: .62rem; font-weight: 700; letter-spacing: 0;
        display: inline-flex; align-items: center; justify-content: center;
    }

    /* ---------- Conteneur ---------- */
    .container { position: relative; z-index: 1; width: 100%; max-width: 940px; margin: 0 auto; padding: 108px 20px 70px; }
    .container.narrow { max-width: 480px; }
    .container.wide { max-width: 1180px; }
    .container.center { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; }

    .card {
        background: var(--card-bg); border: 1px solid var(--card-border); position: relative;
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        padding: 36px 34px; margin-bottom: 20px; box-shadow: 0 16px 40px rgba(0,0,0,.10);
    }
    .card, .msg-card, .modal-content { overflow-wrap: break-word; word-wrap: break-word; min-width: 0; }
    .card > *, .flex-row > *, .row > *, .field-row > *, .status > * { min-width: 0; }
    p, li, td, th, label, .msg-body, .status-text, .hint, .notice { overflow-wrap: break-word; }
    select, input, textarea { max-width: 100%; text-overflow: ellipsis; }
    .card.tight { padding: 26px 28px; }
    .card.center-text { text-align: center; }

    .badge-header { display: inline-block; font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px;
                    margin-bottom: 18px; color: var(--text-muted); border-left: 2px solid var(--text-main); padding-left: 10px; }
    h1, h2, h3 { font-family: 'Syne', sans-serif; text-transform: uppercase; letter-spacing: -.3px; line-height: 1.1; }
    h1 { overflow-wrap: anywhere; font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 800; margin-bottom: 18px; letter-spacing: -1px; }
    h2 { font-size: clamp(1.4rem, 3.4vw, 2rem); font-weight: 800; margin-bottom: 14px; }
    h3 { font-size: 1.05rem; font-weight: 800; margin-bottom: 14px; letter-spacing: .5px; }
    .hero-title { font-size: clamp(2.6rem, 9vw, 5.2rem); overflow-wrap: normal; }
    .text-gradient { background: linear-gradient(135deg, var(--text-main) 30%, var(--text-muted) 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
    p { line-height: 1.7; color: var(--text-muted); }
    .muted { color: var(--text-muted); }
    .small { font-size: .85rem; }
    .mono { font-family: 'JetBrains Mono', 'Courier New', monospace; }
    hr { border: 0; border-top: 1px solid var(--card-border); margin: 22px 0; }

    .flex-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .grid-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 20px; margin-bottom: 20px; }
    .grid-stats .card { margin-bottom: 0; }
    .stat-num { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.8rem; line-height: 1; }

    /* ---------- Boutons carrés ---------- */
    .btn {
        text-decoration: none; padding: 15px 28px; font-family: inherit; font-weight: 700; font-size: .8rem;
        text-transform: uppercase; letter-spacing: 1.2px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
        cursor: pointer; border: 1px solid transparent; border-radius: 0; white-space: normal; text-align: center; line-height: 1.25; position: relative;
        transition: transform .2s ease, background-color .2s ease, color .2s ease, border-color .2s ease, opacity .2s;
    }
    .btn:hover { transform: translateY(-3px); }
    .btn:active { transform: translateY(0); }
    .btn:focus-visible, .tab:focus-visible, .icon-btn:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible { outline: 2px solid var(--text-main); outline-offset: 2px; }
    .btn-primary { background: var(--btn-primary-bg); color: var(--btn-primary-text); border-color: var(--btn-primary-bg); }
    .btn-primary:hover { opacity: .88; }
    .btn-secondary { background: transparent; color: var(--text-main); border-color: var(--btn-secondary-border); }
    .btn-secondary:hover { background: var(--btn-primary-bg); color: var(--btn-primary-text); }
    .btn-danger { background: transparent; color: var(--err); border-color: var(--err); }
    .btn-danger:hover { background: var(--err); color: #fff; }
    td .btn, .btn-sm { white-space: nowrap; }
    .btn-sm { padding: 9px 14px; font-size: .7rem; letter-spacing: 1px; }
    .btn-block { width: 100%; }
    .btn[disabled] { opacity: .45; cursor: not-allowed; transform: none; }

    /* ---------- Champs ---------- */
    input, select, textarea {
        font-family: inherit; font-size: .92rem; padding: 13px 14px; border-radius: 0;
        border: 1px solid var(--card-border); background: var(--input-bg); color: var(--text-main); outline: none; transition: border-color .2s;
    }
    input:hover, select:hover, textarea:hover, input:focus, select:focus, textarea:focus { border-color: var(--text-muted); }
    input[type=checkbox] { width: 20px; height: 20px; padding: 0; accent-color: var(--btn-primary-bg); flex: none; }
    input[type=file] { width: 100%; padding: 10px; }
    input[type=file]::file-selector-button { font-family: inherit; font-weight: 700; text-transform: uppercase; font-size: .7rem; letter-spacing: 1px;
        background: var(--btn-primary-bg); color: var(--btn-primary-text); border: 0; padding: 8px 14px; margin-right: 12px; cursor: pointer; }
    .field { margin-bottom: 16px; }
    .field label, .label { display: block; margin-bottom: 7px; font-size: .7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); }
    .field input, .field select, .field textarea { width: 100%; }
    .field-row { display: flex; gap: 10px; flex-wrap: wrap; }
    .field-row > input, .field-row > select { flex: 1; min-width: 160px; }
    .check { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; cursor: pointer; }

    /* ---------- Étiquettes / statuts ---------- */
    .tag, .user-tag { display: inline-block; padding: 5px 11px; background: var(--tag-bg); border: 1px solid var(--tag-border);
        font-size: .7rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: var(--text-main); }
    .role-Admin { border-color: var(--err); color: var(--err); }
    .role-Collaborateur { border-color: var(--ok); color: var(--ok); }
    .role-None { color: var(--text-muted); }
    .tag-ok { border-color: var(--ok); color: var(--ok); }
    .tag-err { border-color: var(--err); color: var(--err); }

    .status { display: flex; align-items: center; gap: 14px; margin-bottom: 26px; }
    .status .dot { width: 14px; height: 14px; background: var(--err); flex: none; }
    .status .dot.on { background: var(--ok); animation: pulse 1.6s ease-in-out infinite; }
    @keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(74,222,128,.55); } 50% { box-shadow: 0 0 0 9px rgba(74,222,128,0); } }
    .status-text { font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; font-size: .85rem; }
    .status-text small { display: block; font-weight: 400; letter-spacing: .5px; text-transform: none; color: var(--text-muted); font-size: .82rem; margin-top: 3px; }
    .notice { padding: 16px 18px; border: 1px solid var(--err); background: rgba(248,113,113,.08); font-size: .92rem; }
    .hint { font-size: .8rem; color: var(--text-muted); margin-top: 14px; border-left: 2px solid var(--card-border); padding-left: 10px; }

    /* ---------- Tables ---------- */
    .table-responsive { overflow-x: auto; -webkit-overflow-scrolling: touch; margin-top: 8px; }
    table { width: 100%; border-collapse: collapse; min-width: 560px; }
    th, td { padding: 13px 14px; text-align: left; border-bottom: 1px solid var(--card-border); font-size: .9rem; vertical-align: middle; }
    th { font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); white-space: nowrap; }
    tbody tr:hover, tr:hover td { background: var(--row-hover); }
    th:hover { background: transparent; }
    td .row { flex-wrap: nowrap; }
    td.date { white-space: nowrap; color: var(--text-muted); font-size: .8rem; }

    /* ---------- Console ---------- */
    .console-window { background: var(--console-bg); border: 1px solid var(--card-border); padding: 16px; height: 360px; overflow-y: auto;
        font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 12.5px; line-height: 1.6; color: var(--console-text); text-align: left; word-break: break-word; }
    .console-window:empty::before { content: '> en attente…'; color: rgba(255,255,255,.35); }

    /* ---------- Sous-navigation Administration ---------- */
    .admin-nav-bar { display: flex; flex-wrap: nowrap; overflow-x: auto; border: 1px solid var(--card-border); margin-top: 22px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .admin-nav-bar::-webkit-scrollbar { display: none; }
    .subtab { position: relative; flex: 1 0 auto; text-align: center; text-decoration: none; padding: 13px 18px; font-size: .7rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1.3px; color: var(--text-muted); border-right: 1px solid var(--card-border); white-space: nowrap; transition: background-color .2s, color .2s; }
    .subtab:last-child { border-right: 0; }
    .subtab:hover { color: var(--text-main); background: var(--row-hover); }
    .subtab.active { background: var(--btn-primary-bg); color: var(--btn-primary-text); }
    .subtab .badge-dot { top: 50%; transform: translateY(-50%); right: 6px; }

    .msg-card { border: 1px solid var(--card-border); padding: 20px 22px; margin-top: 14px; background: var(--tag-bg); }
    .msg-card.unread { border-color: var(--err); }
    .msg-body { margin-top: 12px; white-space: pre-wrap; color: var(--text-main); }
    .editor { width: 100%; height: 480px; font-family: 'JetBrains Mono','Courier New',monospace; font-size: 13px; line-height: 1.55; background: var(--console-bg); color: var(--console-text); resize: vertical; }
    .avatar { width: 96px; height: 96px; object-fit: cover; border: 1px solid var(--card-border); display: block; margin: 0 auto 18px; }

    /* ---------- Fenêtre modale ---------- */
    .modal-overlay { display: none; position: fixed; inset: 0; z-index: 150; background: rgba(0,0,0,.6); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); justify-content: center; align-items: center; padding: 20px; }
    .modal-overlay.open { display: flex; }
    .modal-content { width: 100%; max-width: 440px; background: var(--toast-bg); border: 1px solid var(--card-border); padding: 30px; animation: pop .25s ease; }
    @keyframes pop { from { transform: translateY(14px); opacity: 0; } to { transform: none; opacity: 1; } }

    /* ---------- Notifications (toasts) : entrent par le bord droit ---------- */
    #toasts { position: fixed; top: 92px; right: 0; z-index: 200; width: min(400px, 100vw); padding: 0 16px 0 0;
              display: flex; flex-direction: column; gap: 10px; pointer-events: none; }
    .toast { pointer-events: auto; position: relative; overflow: hidden; display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: start;
        background: var(--toast-bg); border: 1px solid var(--card-border); border-left: 4px solid var(--accent, var(--info));
        padding: 14px 14px 16px 16px; box-shadow: 0 18px 40px rgba(0,0,0,.28);
        transform: translateX(115%); opacity: 0; transition: transform .38s cubic-bezier(.2,.8,.2,1), opacity .3s; }
    .toast.show { transform: translateX(0); opacity: 1; }
    .toast.hide { transform: translateX(115%); opacity: 0; }
    .toast.success { --accent: var(--ok); } .toast.error { --accent: var(--err); } .toast.warn { --accent: var(--warn); } .toast.info { --accent: var(--info); }
    .toast .t-ico { color: var(--accent); width: 20px; height: 20px; margin-top: 1px; }
    .toast .t-title { font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.6px; color: var(--accent); margin-bottom: 3px; }
    .toast .t-msg { font-size: .88rem; line-height: 1.45; color: var(--text-main); word-break: break-word; }
    .toast .t-link { display: inline-block; margin-top: 8px; font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; text-decoration: none; border-bottom: 1px solid var(--text-main); }
    .toast .t-x { background: none; border: 0; color: var(--text-muted); cursor: pointer; font-size: 1.3rem; line-height: 1; padding: 0 2px; }
    .toast .t-x:hover { color: var(--text-main); }
    .toast .t-bar { position: absolute; left: 0; bottom: 0; height: 3px; width: 100%; background: var(--accent); opacity: .7; transform-origin: left; animation: tbar var(--dur, 6s) linear forwards; }
    .toast:hover .t-bar { animation-play-state: paused; }
    @keyframes tbar { from { transform: scaleX(1); } to { transform: scaleX(0); } }

    /* ---------- Mobile ---------- */
    @media (max-width: 900px) { .brand span { display: none; } .tab:not(.active) .lbl { display: none; } .tab { padding: 0 16px; } }
    @media (max-width: 760px) {
        .topbar { grid-template-columns: 1fr auto; gap: 8px; padding: 8px 12px; }
        .brand { display: none; }
        .topbar.bare { grid-template-columns: 1fr auto; }
        .topbar.bare .brand { display: inline-flex; }
        .tabbar { height: 48px; }
        .tab { flex: 1; padding: 0 6px; }
        .tab .lbl { display: none; }
        .tab svg { width: 19px; height: 19px; }
        .icon-btn { width: 48px; height: 48px; }
        .card { backdrop-filter: none; -webkit-backdrop-filter: none; background: var(--toast-bg); }
        .blob { animation: none; }
        .container { padding: 84px 14px 50px; }
        .card { padding: 26px 20px; }
        .btn { padding: 14px 20px; }
        #toasts { top: 70px; width: 100vw; padding: 0 10px 0 0; }
        .console-window { height: 300px; }
        .stat-num { font-size: 2.3rem; }
        .stack-mobile > * { width: 100%; }
        .stack-mobile .btn { width: 100%; }
    }

    /* ---------- Scripts continus (état de santé) ---------- */
    .cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: stretch; margin-bottom: 20px; }
    .cards-grid > .card { margin-bottom: 0; padding: 28px 26px; }
    @media (max-width: 760px) { .cards-grid { grid-template-columns: 1fr; } }
    .svc-item { padding: 14px 0; border-bottom: 1px solid var(--card-border); }
    .svc-item:first-child { padding-top: 0; }
    .svc-item:last-child { border-bottom: 0; padding-bottom: 0; }
    .svc-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    .svc-name { font-weight: 700; }
    .svc-meta { font-size: .8rem; color: var(--text-muted); margin-top: 5px; line-height: 1.5; }
    .svc-err { font-size: .76rem; margin-top: 6px; color: var(--err); font-family: 'JetBrains Mono', 'Courier New', monospace; word-break: break-word; }
    .svc-actions { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
    .tag-warn { border-color: var(--warn); color: var(--warn); }
    .tag-muted { color: var(--text-muted); }
</style>
"""

# ------------------------------------------------------------
# 2. BRIQUES COMMUNES
# ------------------------------------------------------------
def _ico(paths):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + paths + '</svg>')

I_HOME = _ico('<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>')
I_LOGS = _ico('<rect x="3" y="4" width="18" height="16"/><path d="M7 9l3 3-3 3"/><path d="M13 15h4"/>')
I_USER = _ico('<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>')
I_ADMIN = _ico('<path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>')
I_EXIT = _ico('<path d="M9 21H4V3h5"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>')
I_LOGIN = _ico('<path d="M15 3h5v18h-5"/><path d="M8 7l-5 5 5 5"/><path d="M3 12h12"/>')
I_SUN = _ico('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>').replace('<svg', '<svg class="i-sun"', 1)
I_MOON = _ico('<path d="M21 13.2A9 9 0 1110.8 3a7 7 0 0010.2 10.2z"/>').replace('<svg', '<svg class="i-moon"', 1)

I_AUTO = _ico('<rect x="3" y="4" width="18" height="12"/><path d="M8 20h8M12 16v4"/>').replace('<svg', '<svg class="i-auto"', 1)

_THEME_BTN = ('<button class="icon-btn" id="themeToggle" type="button" aria-label="Changer le thème" title="Thème">'
              + I_AUTO + I_SUN + I_MOON + '</button>')

_BRAND = ('<a class="brand" href="{{ url_for(\'dashboard.index\') }}">'
          '<img src="{{ url_for(\'static\', filename=\'avatar_botjanus.jpeg\') }}" alt=""><span>BotJanus</span></a>')

NAV_FULL = (r"""
<header class="topbar">
  """ + _BRAND + r"""
  <nav class="tabbar" aria-label="Navigation principale">
    <a class="tab {{ 'active' if tab == 'home' }}" href="{{ url_for('dashboard.index') }}" title="{{ t('nav_home') }}">""" + I_HOME + r"""<span class="lbl">{{ t('nav_home') }}</span></a>
    <a class="tab {{ 'active' if tab == 'logs' }}" href="{{ url_for('dashboard.history') }}" title="{{ t('nav_logs') }}">""" + I_LOGS + r"""<span class="lbl">{{ t('nav_logs') }}</span></a>
    {% if session.get('user_id') %}
      <a class="tab {{ 'active' if tab == 'account' }}" href="{{ url_for('auth.account') }}" title="{{ t('nav_account') }}">""" + I_USER + r"""<span class="lbl">{{ t('nav_account') }}</span></a>
      {% if nav_role == 'Admin' %}
      <a class="tab {{ 'active' if tab == 'admin' }}" href="{{ url_for('admin.admin_users') }}" title="{{ t('nav_admin') }}">""" + I_ADMIN + r"""<span class="lbl">{{ t('nav_admin') }}</span>
        <span class="badge-dot" id="adminBadge" {% if not unread_messages %}hidden{% endif %}>{{ unread_messages }}</span></a>
      {% endif %}
      <a class="tab exit" href="{{ url_for('auth.logout') }}" title="{{ t('nav_logout') }}" aria-label="{{ t('nav_logout') }}">""" + I_EXIT + r"""</a>
    {% else %}
      <a class="tab {{ 'active' if tab == 'login' }}" href="{{ url_for('auth.login_wiki') }}" title="{{ t('nav_login') }}">""" + I_LOGIN + r"""<span class="lbl">{{ t('nav_login') }}</span></a>
    {% endif %}
  </nav>
  <div class="tools">""" + _THEME_BTN + r"""</div>
</header>
""")

NAV_BARE = (r"""
<header class="topbar bare">
  """ + _BRAND + r"""
  <div class="tools">""" + _THEME_BTN + r"""</div>
</header>
""")

BACKGROUND = '<div class="gradient-bg"><div class="blob blob-1"></div><div class="blob blob-2"></div><div class="blob blob-3"></div></div>'

# JS commun à TOUTES les pages : thème, toasts (flash + événements serveur), sondage de statut
SHELL_JS = r"""
<div id="toasts" role="status" aria-live="polite"></div>
<script>
(function () {
  var html = document.documentElement;
  var LANG = (html.getAttribute('lang') || 'fr').slice(0, 2);
  var TITLES = {
    fr: { success: 'Succès', error: 'Erreur', warn: 'Attention', info: 'Information' },
    en: { success: 'Success', error: 'Error', warn: 'Warning', info: 'Information' }
  }[LANG] || {};
  var ICONS = {
    success: '<path d="M20 6L9 17l-5-5"/>',
    error: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.01"/>',
    warn: '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/>'
  };

  /* ----- Thème ----- */
  var tt = document.getElementById('themeToggle');
  var NAMES = LANG === 'en' ? { auto: 'Theme: automatic (system)', light: 'Theme: light', dark: 'Theme: dark' } : { auto: 'Thème : automatique (système)', light: 'Thème : clair', dark: 'Thème : sombre' };
  function themeLabel() { if (tt) { var m = window.bjGetMode(); tt.title = NAMES[m]; tt.setAttribute('aria-label', NAMES[m]); } }
  themeLabel();
  if (tt) tt.addEventListener('click', function () {
    var next = { auto: 'light', light: 'dark', dark: 'auto' }[window.bjGetMode()];
    window.bjSetMode(next); themeLabel();
    window.toast(NAMES[next], { type: 'info', title: LANG === 'en' ? 'Theme' : 'Thème', duration: 2200 });
  });

  /* ----- Toasts : window.toast(message, {type, title, href, linkText, duration}) ----- */
  var box = document.getElementById('toasts');
  window.toast = function (msg, o) {
    o = o || {};
    var type = o.type || 'info', dur = o.duration || (type === 'error' ? 9000 : 6000);
    var el = document.createElement('div');
    el.className = 'toast ' + type;
    el.style.setProperty('--dur', dur + 'ms');
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none'); svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2'); svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('class', 't-ico'); svg.innerHTML = ICONS[type] || ICONS.info;
    var body = document.createElement('div');
    var ti = document.createElement('div'); ti.className = 't-title'; ti.textContent = o.title || TITLES[type] || '';
    var ms = document.createElement('div'); ms.className = 't-msg'; ms.textContent = msg;
    body.appendChild(ti); body.appendChild(ms);
    if (o.href) {
      var a = document.createElement('a'); a.className = 't-link'; a.href = o.href; a.textContent = o.linkText || 'Voir';
      body.appendChild(a);
    }
    var x = document.createElement('button'); x.type = 'button'; x.className = 't-x'; x.setAttribute('aria-label', 'Fermer'); x.innerHTML = '&times;';
    var bar = document.createElement('div'); bar.className = 't-bar';
    el.appendChild(svg); el.appendChild(body); el.appendChild(x); el.appendChild(bar);
    box.appendChild(el);
    requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add('show'); }); });
    var closed = false;
    function close() {
      if (closed) return; closed = true;
      el.classList.remove('show'); el.classList.add('hide');
      setTimeout(function () { el.remove(); }, 420);
    }
    x.addEventListener('click', close);
    bar.addEventListener('animationend', close);
    return close;
  };

  /* ----- Messages flash Flask -> toasts (toutes les pages) ----- */
  function classify(m) {
    if (/banni|banned|insuffisant|[ée]chec|failed|erreur|error|impossible|unable|refus|denied|incorrect|invalide|invalid|expir|introuvable|not found|manquant|missing|vide|empty/i.test(m)) return 'error';
    if (/succ[eè]s|success|r[ée]ussi|cr[ée][ée]|modifi[ée]|enregistr|envoy|sent|saved|supprim[ée]|deleted|lié|linked|termin[ée]e|✅/i.test(m)) return 'success';
    if (/veuillez|please|d[ée]j[àa]|already|verrouill|locked|d[ée]sactiv/i.test(m)) return 'warn';
    return 'info';
  }
  var FLASH = {{ get_flashed_messages()|tojson }};
  FLASH.forEach(function (m, i) { setTimeout(function () { window.toast(m.replace(/^[^\p{L}\p{N}]+/u, ''), { type: classify(m) }); }, 250 + i * 180); });

  /* ----- Événements serveur : script terminé / lancé, nouveaux messages ----- */
  if (document.body.getAttribute('data-poll') === 'off') return;
  function ss(k, v) { try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch (e) {} return null; }
  var L = LANG === 'en'
    ? { done: 'Script finished', doneMsg: function (n) { return "'" + n + "' has completed."; }, start: 'Script started', startMsg: function (n) { return "'" + n + "' is now running."; }, msg: 'New message', msgs: function (n) { return n + ' unread message(s).'; }, see: 'Open' }
    : { done: 'Script terminé', doneMsg: function (n) { return "Le traitement de '" + n + "' s'est achevé."; }, start: 'Script lancé', startMsg: function (n) { return "'" + n + "' est en cours d'exécution."; }, msg: 'Nouveau message', msgs: function (n) { return n + ' message(s) non lu(s).'; }, see: 'Ouvrir' };

  function poll() {
    fetch('/api/status_json', { credentials: 'same-origin', headers: { Accept: 'application/json' } })
      .then(function (r) { if (!r.ok || (r.headers.get('content-type') || '').indexOf('json') < 0) throw 0; return r.json(); })
      .then(function (s) {
        var prev = ss('bj_run'), prevName = ss('bj_name') || s.script_name;
        if (prev === '1' && !s.running) {
          window.toast(L.doneMsg(prevName), { type: 'success', title: L.done });
          if (window.Notification && Notification.permission === 'granted') {
            try { new Notification('BotJanus — ' + L.done, { body: L.doneMsg(prevName), icon: '/static/avatar_botjanus.jpeg' }); } catch (e) {}
          }
        } else if (prev === '0' && s.running) {
          window.toast(L.startMsg(s.script_name), { type: 'info', title: L.start });
        }
        ss('bj_run', s.running ? '1' : '0'); ss('bj_name', s.script_name);

        var badge = document.getElementById('adminBadge');
        if (badge) { badge.textContent = s.unread; badge.hidden = !s.unread; }
        var pu = ss('bj_unread');
        if (s.role === 'Admin' && pu !== null && s.unread > parseInt(pu, 10)) {
          window.toast(L.msgs(s.unread), { type: 'info', title: L.msg, href: '/admin/messages', linkText: L.see });
        }
        ss('bj_unread', String(s.unread || 0));
      })
      .catch(function () {});
  }
  poll(); setInterval(poll, 4000);
})();
</script>
"""


def _page(title, body, tab=None, nav="full", wide="", poll=True, extra_head="", extra_js=""):
    """Assemble une page complète (chaîne Jinja) : head, fond, barre d'onglets, contenu, JS commun."""
    tab_line = "{% set tab = '" + (tab or "") + "' %}"
    return (
        '<!DOCTYPE html>\n<html lang="{{ current_lang }}" data-theme="dark">\n<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '  <title>' + title + '</title>\n'
        '  <link rel="icon" type="image/jpeg" href="{{ url_for(\'static\', filename=\'avatar_botjanus_rounded.png\') }}">\n'
        '  {{ glass_css|safe }}\n' + extra_head + '\n</head>\n'
        '<body' + ('' if poll else ' data-poll="off"') + '>\n' + tab_line + '\n'
        + BACKGROUND + '\n' + (NAV_FULL if nav == "full" else NAV_BARE) + '\n'
        '<main class="container ' + wide + '">\n' + body + '\n</main>\n'
        + SHELL_JS + extra_js + '\n</body>\n</html>\n'
    )


# ------------------------------------------------------------
# 3. PAGES
# ------------------------------------------------------------
_DASH_BODY = r"""
  <div style="padding:0 4px 10px;">
    <span class="badge-header">{{ t('nav_home') }}</span>
    <h1 class="hero-title" style="margin-bottom:6px;">Bot<span class="text-gradient">Janus</span></h1>
  </div>

  <div class="cards-grid">
  <section class="card">
    <span class="badge-header">{{ t('card_temp') }}</span>

    <div class="status">
      <span class="dot {{ 'on' if running }}"></span>
      <div class="status-text">
        {% if running %}{{ t('status_running')|replace('🟢 ', '') }}{{ script_name }}{% else %}{{ t('status_stopped')|replace('🔴 ', '') }}{% endif %}
      </div>
    </div>

    {% if running %}
        {% if role in ['Collaborateur', 'Admin'] %}
            <form action="{{ url_for('dashboard.stop_script') }}" method="post">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <button class="btn btn-danger" type="submit">{{ t('btn_stop') }}</button>
            </form>
        {% elif session.get('user_id') %}
            <p>{{ t('script_running') }}</p>
        {% else %}
            <p style="margin-bottom:22px;">{{ t('script_running') }} {{ t('login_required') }}</p>
            <div class="row stack-mobile">
                <a href="{{ url_for('auth.login_wiki') }}" class="btn btn-primary">{{ t('login_wiki') }}</a>
                <a href="{{ url_for('auth.manual_login_page') }}" class="btn btn-secondary">{{ t('login_manual') }}</a>
            </div>
        {% endif %}
    {% else %}
        {% if session.get('user_id') %}
            {# Tout utilisateur connecté VOIT l'interface de lancement (y compris rôle None).
               Seuls Collaborateur/Admin peuvent réellement lancer : pour un None, la
               vérification autopatrol multi-wikis est faite côté serveur au clic sur
               DÉMARRER (dashboard.start_script) ; si elle réussit, il est promu
               Collaborateur en base et le script part. Sinon : message via flash(). #}
            {% if locked == '1' and role != 'Admin' %}
                <div class="notice">{{ t('locked_msg') }}</div>
            {% else %}
                <form id="startForm" action="{{ url_for('dashboard.start_script') }}" method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <input type="hidden" name="arg_lang" id="hidden_lang">
                    <input type="hidden" name="arg_cat" id="hidden_cat">
                    <input type="hidden" name="arg_portal" id="hidden_portal">
                    <div class="field-row">
                        <select id="scriptSelect" name="choice" aria-label="Script">
                            {% for s in available_scripts %}
                                <option value="{{ s.filename }}">{{ s.filename }}{% if role == 'Admin' and s.is_active == 0 %} (Verrouillé aux Users){% endif %}</option>
                            {% endfor %}
                        </select>
                        <button class="btn btn-primary" type="button" onclick="handleStart()">{{ t('btn_start') }}</button>
                    </div>
                </form>
                {% if role not in ['Collaborateur', 'Admin'] %}
                    <p class="hint">{{ t('launch_hint') }}</p>
                {% endif %}
            {% endif %}
        {% else %}
            <p style="margin-bottom:22px;">{{ t('login_required') }}</p>
            <div class="row stack-mobile">
                <a href="{{ url_for('auth.login_wiki') }}" class="btn btn-primary">{{ t('login_wiki') }}</a>
                <a href="{{ url_for('auth.manual_login_page') }}" class="btn btn-secondary">{{ t('login_manual') }}</a>
            </div>
        {% endif %}
    {% endif %}
  </section>

  <section class="card">
    <span class="badge-header">{{ t('card_cont') }}</span>
    <div id="contList"><p class="small">…</p></div>
    {% if role == 'Admin' %}
        <a href="{{ url_for('services.admin_services') }}" class="btn btn-secondary btn-sm" style="margin-top:18px;">{{ t('manage') }}</a>
    {% endif %}
  </section>
  </div>

  <section class="card">
    <div class="flex-row" style="margin-bottom:16px;">
        <h3 style="margin:0;">{{ t('console') }}</h3>
        <a href="{{ url_for('dashboard.history') }}" class="btn btn-secondary btn-sm">{{ t('history')|replace('📂 ', '') }}</a>
    </div>
    <div class="console-window" id="logBox">{% for line in logs %}<div>{{ line }}</div>{% endfor %}</div>
  </section>

  <div id="portalModal" class="modal-overlay" onclick="if(event.target===this)closeModal()">
      <div class="modal-content">
          <span class="badge-header">Portail</span>
          <h3>Configuration Portail Bot</h3>
          <div class="field">
              <label for="modal_lang">Langue Vikidia</label>
              <select id="modal_lang">
                  <option value="fr">Français (fr)</option>
                  <option value="en">English (en)</option>
              </select>
          </div>
          <div class="field">
              <label for="modal_cat">Nom de la Catégorie</label>
              <input type="text" id="modal_cat" placeholder="Ex: Histoire de France">
          </div>
          <div class="field">
              <label for="modal_portal">Nom du Portail à ajouter</label>
              <input type="text" id="modal_portal" placeholder="Ex: France">
          </div>
          <div class="row" style="justify-content:flex-end; margin-top:24px;">
              <button class="btn btn-secondary" type="button" onclick="closeModal()">Annuler</button>
              <button class="btn btn-primary" type="button" onclick="confirmPortalLaunch()">Lancer</button>
          </div>
      </div>
  </div>
"""

_DASH_JS = r"""
<script>
    var logBox = document.getElementById("logBox");
    if (logBox) {
        logBox.scrollTop = logBox.scrollHeight;
        setInterval(function () {
            fetch("/api/live_logs").then(function (r) { return r.text(); }).then(function (data) {
                var isScrolled = logBox.scrollHeight - logBox.clientHeight <= logBox.scrollTop + 50;
                logBox.innerHTML = data;
                if (isScrolled) logBox.scrollTop = logBox.scrollHeight;
            }).catch(function () {});
        }, 2000);
    }
    {% if session.get('user_id') %}
    // Notifications navigateur (fin de script), demandées uniquement aux utilisateurs connectés
    if (window.Notification && Notification.permission === "default") { Notification.requestPermission(); }
    {% endif %}


    /* ---- Carte "scripts continus" ---- */
    var SVC_LABELS = {ok: "En marche", degraded: "Dégradé", down: "Hors service", stopped: "Arrêté"};
    var SVC_CLS = {ok: "tag-ok", degraded: "tag-warn", down: "tag-err", stopped: "tag-muted"};
    function fmtDur(sec) {
        if (sec == null) return "—";
        var d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600), m = Math.floor(sec % 3600 / 60);
        return d ? d + " j " + h + " h" : h ? h + " h " + m + " min" : m + " min";
    }
    function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
    function renderServices(res) {
        var box = document.getElementById("contList");
        if (!box) return;
        box.textContent = "";
        if (!res.reachable) { box.appendChild(el("div", "notice", res.error || "Serveur distant injoignable.")); return; }
        if (!res.services.length) { box.appendChild(el("p", "small", "Aucun script continu configuré.")); return; }
        res.services.forEach(function (s) {
            var item = el("div", "svc-item"), head = el("div", "svc-head");
            head.appendChild(el("span", "svc-name", s.label));
            head.appendChild(el("span", "tag " + (SVC_CLS[s.health] || ""), SVC_LABELS[s.health] || s.health));
            item.appendChild(head);
            var parts = [s.health_reason];
            if (s.running) parts.push("actif depuis " + fmtDur(s.uptime_s));
            if (s.heartbeat_age_s != null) parts.push("dernière activité il y a " + fmtDur(s.heartbeat_age_s));
            item.appendChild(el("div", "svc-meta", parts.join(" · ")));
            if (res.is_admin && s.last_error) item.appendChild(el("div", "svc-err", (s.last_error.time || "") + " " + s.last_error.message));
            box.appendChild(item);
        });
    }
    function refreshServices() {
        fetch("/api/services/status").then(function (r) { return r.json(); }).then(renderServices)
            .catch(function () { renderServices({reachable: false, error: "Dashboard injoignable."}); });
    }
    refreshServices(); setInterval(refreshServices, 10000);

    function handleStart() {
        var choice = document.getElementById('scriptSelect').value;
        if (choice.includes('portal.py') || choice === 'Portail') {
            document.getElementById('portalModal').classList.add('open');
        } else {
            document.getElementById('startForm').submit();
        }
    }
    function closeModal() { document.getElementById('portalModal').classList.remove('open'); }
    function confirmPortalLaunch() {
        document.getElementById('hidden_lang').value = document.getElementById('modal_lang').value;
        document.getElementById('hidden_cat').value = document.getElementById('modal_cat').value;
        document.getElementById('hidden_portal').value = document.getElementById('modal_portal').value;
        document.getElementById('startForm').submit();
        closeModal();
    }
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });
</script>
"""

DASHBOARD_HTML = _page("BotJanus", _DASH_BODY, tab="home", extra_js=_DASH_JS)

GATE_HTML = _page("Sécurité - BotJanus", r"""
  <section class="card center-text">
    <span class="badge-header">Sécurité</span>
    <h2>Portail de sécurité</h2>
    <p style="margin-bottom:24px;">Validez le captcha pour accéder au site.</p>
    <form action="{{ url_for('auth.verify_gate') }}" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <div class="g-recaptcha" data-sitekey="{{ site_key }}" style="display:inline-block; margin-bottom:22px;"></div>
        <button type="submit" class="btn btn-primary btn-block">Entrer sur le site</button>
    </form>
  </section>
""", nav="bare", wide="narrow center", poll=False,
    extra_head='<script src="https://www.google.com/recaptcha/api.js" async defer></script>')

LOGIN_MANUAL_HTML = _page("{{ t('login_title') }}", r"""
  <section class="card">
    <span class="badge-header">{{ t('login_manual') }}</span>
    <h2>{{ t('login_title') }}</h2>
    <form action="{{ url_for('auth.manual_login_post') }}" method="POST" style="margin-top:22px;">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <div class="field"><label for="username">{{ t('username_ph') }}</label><input id="username" type="text" name="username" autocomplete="username" required></div>
        <div class="field"><label for="password">{{ t('password_ph') }}</label><input id="password" type="password" name="password" autocomplete="current-password" required></div>
        <button class="btn btn-primary btn-block" type="submit">{{ t('connect_btn') }}</button>
    </form>
    <a href="{{ url_for('dashboard.index') }}" class="btn btn-secondary btn-block" style="margin-top:12px;">{{ t('back') }}</a>
  </section>
""", nav="bare", wide="narrow center")

ACCOUNT_HTML = _page("{{ t('nav_account') }}", r"""
  <section class="card center-text">
    <img class="avatar" src="{{ user.avatar }}" alt="">
    <span class="badge-header">{{ t('nav_account') }}</span>
    <h1 style="margin-bottom:14px;">{{ user.username }}</h1>
    <p class="small" style="margin-bottom:26px;">{{ t('role_tag') }} : <span class="user-tag role-{{ user.role }}">{{ user.role }}</span></p>

    <div class="field" style="max-width:320px; margin:0 auto 26px; text-align:left;">
        <label for="lang-select">{{ t('lang_tag') }}</label>
        <select id="lang-select" onchange="window.location.href = '{{ url_for('auth.set_language', code='') }}' + this.value">
            <option value="fr" {{ 'selected' if current_lang == 'fr' else '' }}>Français</option>
            <option value="en" {{ 'selected' if current_lang == 'en' else '' }}>English</option>
        </select>
    </div>

    <hr>
    <div class="row stack-mobile" style="justify-content:center;">
        <a href="{{ url_for('contact.contact_form') }}" class="btn btn-secondary">{{ t('contact')|replace('✉️ ', '') }}</a>
        <a href="{{ url_for('auth.logout') }}" class="btn btn-danger">{{ t('logout') }}</a>
    </div>
  </section>
""", tab="account", wide="narrow")

CONTACT_HTML = _page("Contact - BotJanus", r"""
  <section class="card">
    <span class="badge-header">{{ t('contact')|replace('✉️ ', '') }}</span>
    <h2>Contacter l'administrateur</h2>
    <p class="small" style="margin-bottom:22px;">Un problème, une question, une suggestion ? Envoyez un message, il sera transmis directement à l'administrateur.</p>
    <form action="{{ url_for('contact.contact_form') }}" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <div class="field"><textarea name="content" placeholder="Votre message…" required style="height:170px; resize:vertical;"></textarea></div>
        <button type="submit" class="btn btn-primary btn-block">Envoyer</button>
    </form>
    <a href="{{ url_for('auth.account') }}" class="btn btn-secondary btn-block" style="margin-top:12px;">{{ t('back') }}</a>
  </section>
""", tab="account", wide="narrow")

# Sous-navigation de l'espace Administration (variable Jinja `active` fournie par les routes)
ADMIN_NAV = r"""
<nav class="admin-nav-bar" aria-label="Administration">
    <a href="{{ url_for('admin.admin_users') }}" class="subtab {{ 'active' if active == 'users' }}">Utilisateurs</a>
    <a href="{{ url_for('admin.admin_scripts') }}" class="subtab {{ 'active' if active == 'scripts' }}">Scripts</a>
    <a href="{{ url_for('admin.admin_schedules') }}" class="subtab {{ 'active' if active == 'schedules' }}">Planification</a>
    <a href="{{ url_for('services.admin_services') }}" class="subtab {{ 'active' if active == 'services' }}">Scripts continus</a>
    <a href="{{ url_for('admin.admin_stats') }}" class="subtab {{ 'active' if active == 'stats' }}">Statistiques</a>
    <a href="{{ url_for('admin.settings') }}" class="subtab {{ 'active' if active == 'settings' }}">Système</a>
    <a href="{{ url_for('contact.admin_messages') }}" class="subtab {{ 'active' if active == 'messages' }}" style="padding-right:34px;">Messages
        {% if unread_messages and unread_messages > 0 %}<span class="badge-dot">{{ unread_messages }}</span>{% endif %}</a>
</nav>
"""


def _admin_head(title):
    return ('<section class="card">\n<span class="badge-header">Administration</span>\n<h2 style="margin-bottom:0;">'
            + title + '</h2>\n' + ADMIN_NAV + '\n</section>\n')


ADMIN_MESSAGES_HTML = _page("Messages - Admin", _admin_head("Messages reçus") + r"""
  <section class="card">
    {% if not msgs %}<p>Aucun message pour le moment.</p>{% endif %}
    {% for m in msgs %}
    <div class="msg-card {{ 'unread' if not m.is_read }}" {% if loop.first %}style="margin-top:0;"{% endif %}>
        <div class="flex-row">
            <div>
                <b>{{ m.username }}</b>
                {% if not m.is_read %}<span class="user-tag tag-err" style="margin-left:8px;">Nouveau</span>{% endif %}
                <div class="small muted" style="margin-top:3px;">{{ m.date }}</div>
            </div>
            <div class="row">
                {% if not m.is_read %}
                <form action="{{ url_for('contact.mark_read', message_id=m.id) }}" method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <button type="submit" class="btn btn-secondary btn-sm">Marquer comme lu</button>
                </form>
                {% endif %}
                <form action="{{ url_for('contact.delete_message', message_id=m.id) }}" method="POST" onsubmit="return confirm('Supprimer ce message ?');">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <button type="submit" class="btn btn-danger btn-sm">Supprimer</button>
                </form>
            </div>
        </div>
        <p class="msg-body">{{ m.content }}</p>
    </div>
    {% endfor %}
  </section>
""", tab="admin")

ADMIN_SCRIPTS_HTML = _page("Scripts - Administration", _admin_head("Scripts") + r"""
  <section class="card">
    <h3>Créer un script (.py)</h3>
    <form action="{{ url_for('admin.admin_create_script') }}" method="POST" class="field-row">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <input type="text" name="filename" placeholder="Ex: mon_bot.py" required>
        <button type="submit" class="btn btn-primary">Créer</button>
    </form>
  </section>

  <section class="card">
    <h3>Liste des scripts (/bots)</h3>
    <div class="table-responsive">
        <table>
            <thead><tr><th>Nom du fichier</th><th>Accès collaborateurs</th><th>Actions</th></tr></thead>
            <tbody>
            {% for script in scripts %}
            <tr>
                <td><b>{{ script }}</b></td>
                <td>
                    {% set is_active = configs.get(script, 1) %}
                    <span class="user-tag {{ 'tag-ok' if is_active == 1 else 'tag-err' }}">{{ 'Disponible' if is_active == 1 else 'Masqué' }}</span>
                </td>
                <td>
                    <div class="row">
                        <form action="{{ url_for('admin.admin_toggle_script') }}" method="POST">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                            <input type="hidden" name="filename" value="{{ script }}">
                            <input type="hidden" name="current_val" value="{{ is_active }}">
                            <button type="submit" class="btn btn-secondary btn-sm">Changer droits</button>
                        </form>
                        <a href="{{ url_for('admin.admin_edit_script_page', filename=script) }}" class="btn btn-secondary btn-sm">Éditer</a>
                        <form action="{{ url_for('admin.admin_run_script_direct') }}" method="POST">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                            <input type="hidden" name="filename" value="{{ script }}">
                            <button type="submit" class="btn btn-primary btn-sm">Run direct</button>
                        </form>
                    </div>
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
  </section>
""", tab="admin")

SCRIPT_EDITOR_HTML = _page("Éditeur - {{ filename }}", r"""
  <section class="card">
    <div class="flex-row" style="margin-bottom:18px;">
        <div><span class="badge-header" style="margin-bottom:10px;">Éditeur</span><h2 style="margin:0;">{{ filename }}</h2></div>
        <a href="{{ url_for('admin.admin_scripts') }}" class="btn btn-secondary">Retour</a>
    </div>
    <form action="{{ url_for('admin.admin_save_script') }}" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <input type="hidden" name="filename" value="{{ filename }}"/>
        <textarea name="content" class="editor" spellcheck="false">{{ content }}</textarea>
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:14px;">Sauvegarder le script</button>
    </form>
  </section>
""", tab="admin", wide="wide")

SCHEDULES_HTML = _page("Planification - Admin", _admin_head("Planification") + r"""
  <section class="card">
    <h3>Ajouter une tâche</h3>
    <form action="{{ url_for('admin.admin_schedules') }}" method="POST" class="field-row">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <input type="hidden" name="action" value="add"/>
        <select name="script_name">{% for s in scripts %}<option value="{{ s }}">{{ s }}</option>{% endfor %}</select>
        <select name="frequency">
            <option value="minutes">Minutes</option>
            <option value="hours">Heures</option>
            <option value="days">Jours</option>
        </select>
        <input type="number" name="time_value" value="30" min="1" style="max-width:110px; flex:none;">
        <button type="submit" class="btn btn-primary">Créer répétition</button>
    </form>
  </section>

  <section class="card">
    <h3>Planifications actives</h3>
    <div class="table-responsive">
        <table>
            <thead><tr><th>Script</th><th>Intervalle</th><th>Dernier run</th><th>Prochain run</th><th>Action</th></tr></thead>
            <tbody>
            {% for s in schedules %}
            <tr>
                <td><b>{{ s.script_name }}</b></td>
                <td>Toutes les {{ s.time_value }} {{ s.frequency }}</td>
                <td class="date">{{ s.last_run }}</td>
                <td class="date" style="color:var(--ok);">{{ s.next_run }}</td>
                <td>
                    <form action="{{ url_for('admin.admin_schedules') }}" method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <input type="hidden" name="action" value="delete"/>
                        <input type="hidden" name="id" value="{{ s.id }}"/>
                        <button type="submit" class="btn btn-danger btn-sm">Supprimer</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
  </section>
""", tab="admin")

STATS_HTML = _page("Statistiques - Admin", _admin_head("Statistiques") + r"""
  <div class="grid-stats">
    <div class="card"><span class="badge-header">Membres inscrits</span><div class="stat-num">{{ total_users }}</div></div>
    <div class="card"><span class="badge-header">Volume logs</span><div class="stat-num">{{ total_logs }}</div></div>
  </div>

  <section class="card">
    <h3>Activité par module (lignes de logs)</h3>
    <div class="table-responsive">
        <table>
            <thead><tr><th>Nom du module</th><th>Volume d'activité</th></tr></thead>
            <tbody>
            {% for c in script_counts %}
            <tr><td>{{ c.script }}</td><td><b>{{ c.cnt }}</b> lignes</td></tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
  </section>
""", tab="admin")

ADMIN_USERS_HTML = _page("{{ t('users_roles') }}", _admin_head("{{ t('users_roles') }}") + r"""
  <section class="card">
    <div class="table-responsive">
        <table>
            <thead><tr><th>User</th><th>{{ t('role_tag') }}</th><th>{{ t('actions') }}</th></tr></thead>
            <tbody>
            {% for u in users if not u.is_banned %}
            <tr>
                <td><b>{{ u.username }}</b></td>
                <td><span class="user-tag role-{{ u.role }}">{{ u.role }}</span></td>
                <td>
                    <form action="{{ url_for('admin.admin_update_user') }}" method="POST" id="form-{{ u.wiki_id }}" class="row">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <input type="hidden" name="wiki_id" value="{{ u.wiki_id }}">
                        <input type="hidden" name="reason" id="reason-{{ u.wiki_id }}" value="">
                        <input type="hidden" name="action" id="action-{{ u.wiki_id }}" value="update">
                        <select name="new_role" style="padding:9px 10px; font-size:.82rem;">
                            <option value="None" {{ 'selected' if u.role == 'None' else '' }}>None</option>
                            <option value="Collaborateur" {{ 'selected' if u.role == 'Collaborateur' else '' }}>Collaborateur</option>
                            <option value="Admin" {{ 'selected' if u.role == 'Admin' else '' }}>Admin</option>
                        </select>
                        <button type="submit" class="btn btn-secondary btn-sm">{{ t('update') }}</button>
                        <button type="button" onclick="confirmBan('{{ u.wiki_id }}', '{{ u.username }}')" class="btn btn-danger btn-sm">{{ t('ban') }}</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
  </section>
""", tab="admin", extra_js=r"""
<script>
    function confirmBan(userId, username) {
        var reason = prompt("Raison du bannissement pour " + username + " ?");
        if (reason) {
            document.getElementById('reason-' + userId).value = reason;
            document.getElementById('action-' + userId).value = 'ban';
            document.getElementById('form-' + userId).submit();
        }
    }
</script>
""")

SETTINGS_HTML = _page("{{ t('system_settings') }}", _admin_head("{{ t('system_settings') }}") + r"""
  <section class="card">
    <h3>Sauvegardes de données</h3>
    <p class="small" style="margin-bottom:18px;">Exportez les profils ou effectuez une restauration en cas d'anomalie système.</p>
    <a href="{{ url_for('admin.backup_export') }}" class="btn btn-primary">Exporter la base (CSV)</a>
    <hr>
    <form action="{{ url_for('admin.backup_import') }}" method="POST" enctype="multipart/form-data">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <div class="field"><input type="file" name="backup_file" accept=".csv" required></div>
        <button type="submit" class="btn btn-danger">Restaurer le fichier</button>
    </form>
  </section>

  <section class="card">
    <h3>Gestion et nettoyage des logs</h3>
    <form action="{{ url_for('admin.clean_logs_manual') }}" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <p class="small" style="margin-bottom:14px;"><b>Nettoyage ciblé :</b> supprimer définitivement les logs plus anciens que X jours.</p>
        <div class="row">
            <input type="number" name="days" min="0" placeholder="Ex: 7" required style="width:110px;">
            <span class="muted">jours</span>
            <button type="submit" class="btn btn-danger">Supprimer par ancienneté</button>
        </div>
    </form>
    <hr>
    <form action="{{ url_for('admin.delete_all_logs') }}" method="POST"
          onsubmit="return confirm('Supprimer DÉFINITIVEMENT tous les logs ? Cette action est irréversible.');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <p class="small" style="margin-bottom:14px;"><b>Nettoyage total :</b> supprime immédiatement l'intégralité des logs ({{ total_logs }} entrée(s) actuellement).</p>
        <button type="submit" class="btn btn-danger">Supprimer tous les logs</button>
    </form>
  </section>

  <section class="card">
    <h3>{{ t('security') }}</h3>
    <form action="{{ url_for('admin.update_settings') }}" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <label class="check">
            <input type="checkbox" name="lock_launch" value="1" {% if locked == '1' %}checked{% endif %}>
            <span>{{ t('lock_option') }}</span>
        </label>
        <label class="check">
            <input type="checkbox" name="captcha_enabled" value="1" {% if captcha_enabled == '1' %}checked{% endif %}>
            <span>Activer le portail reCAPTCHA Google</span>
        </label>
        <button class="btn btn-primary" type="submit">{{ t('save') }}</button>
    </form>
  </section>
""", tab="admin")

HISTORY_HTML = _page("{{ t('history')|replace('📂 ', '') }}", r"""
  <section class="card">
    <div class="flex-row">
        <div><span class="badge-header" style="margin-bottom:10px;">{{ t('nav_logs') }}</span><h2 style="margin:0;">{{ t('history')|replace('📂 ', '') }}</h2></div>
        <div class="row">
            <a href="{{ url_for('dashboard.export_logs_excel') }}{% if request.args.get('search') %}?search={{ request.args.get('search') }}{% endif %}" class="btn btn-primary btn-sm">Export Excel</a>
            <a href="{{ url_for('dashboard.export_logs_csv') }}{% if request.args.get('search') %}?search={{ request.args.get('search') }}{% endif %}" class="btn btn-secondary btn-sm">Export CSV</a>
        </div>
    </div>
    <form id="filter-form" action="{{ url_for('dashboard.history') }}" method="GET" class="field-row" style="margin-top:22px;">
        <input type="text" name="search" placeholder="Rechercher un message…" value="{{ request.args.get('search', '') }}">
        <button type="submit" class="btn btn-secondary">Rechercher</button>
    </form>
    <p class="small" style="margin-top:12px;">{{ total_count }} entrée(s) trouvée(s) — affichage des 500 plus récentes</p>
    <div class="table-responsive">
        <table>
            <thead><tr><th>Date</th><th>Script</th><th>Message</th></tr></thead>
            <tbody>
            {% for row in rows %}
            <tr>
                <td class="date mono">{{ row[1] }}</td>
                <td><b>{{ row[2] }}</b></td>
                <td>{{ row[3] }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
  </section>
""", tab="logs", wide="wide")


_SVC_ADMIN_JS = r"""
<script>
    var CSRF = document.querySelector('meta[name="csrf-token"]').content;
    var LABELS = {ok: "En marche", degraded: "Dégradé", down: "Hors service", stopped: "Arrêté"};
    var CLS = {ok: "tag-ok", degraded: "tag-warn", down: "tag-err", stopped: "tag-muted"};
    var ACT_LABEL = {start: "démarrage", stop: "arrêt", restart: "relance"};
    var logTimer = null, logId = null, sending = false, watching = {};

    function fmtDur(sec) {
        if (sec == null) return "—";
        var d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600), m = Math.floor(sec % 3600 / 60);
        return d ? d + " j " + h + " h" : h ? h + " h " + m + " min" : m + " min";
    }
    function mk(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

    function act(id, action) {
        if (sending) return;
        if (action === "stop" && !confirm("Arrêter ce script ? Il ne sera pas relancé automatiquement.")) return;
        sending = true;
        fetch("/admin/services/" + encodeURIComponent(id) + "/" + action, {method: "POST", headers: {"X-CSRFToken": CSRF}})
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (j.ok) { watching[j.command_id] = action; window.toast(j.message, {type: "info", title: "Ordre envoyé"}); }
                else window.toast(j.message || "Erreur.", {type: "error"});
            })
            .catch(function () { window.toast("Erreur réseau.", {type: "error"}); })
            .finally(function () { sending = false; load(); });
    }

    function checkResults(services) {
        services.forEach(function (s) {
            var c = s.last_command;
            if (!c || !(c.id in watching)) return;
            if (c.status === "done") { window.toast(s.label + " : " + (ACT_LABEL[c.action] || c.action) + " effectué. " + (c.result || ""), {type: "success"}); delete watching[c.id]; }
            else if (c.status === "failed" || c.status === "expired") { window.toast(s.label + " : " + (c.result || "échec"), {type: "error"}); delete watching[c.id]; }
        });
    }

    function render(res) {
        var box = document.getElementById("svcAdminList"); box.textContent = "";
        document.getElementById("svcStamp").textContent = res.last_contact_age_s != null ? "agent vu il y a " + res.last_contact_age_s + " s" : "";
        if (!res.reachable) { box.appendChild(mk("div", "notice", res.error)); return; }
        if (!res.services.length) { box.appendChild(mk("p", "small", "Aucun script continu configuré.")); return; }
        checkResults(res.services);
        res.services.forEach(function (s) {
            var it = mk("div", "svc-item"), head = mk("div", "svc-head");
            head.appendChild(mk("span", "svc-name", s.label));
            head.appendChild(mk("span", "tag " + (CLS[s.health] || ""), LABELS[s.health] || s.health));
            if (s.pending_action) head.appendChild(mk("span", "tag tag-warn", "⏳ " + (ACT_LABEL[s.pending_action] || s.pending_action) + " en cours"));
            it.appendChild(head);
            if (s.description) it.appendChild(mk("div", "svc-meta", s.description));
            var m = [s.health_reason];
            if (s.running) {
                m.push("PID " + s.pid, "actif depuis " + fmtDur(s.uptime_s));
                if (s.memory_mb != null) m.push(s.memory_mb + " Mo");
                if (s.cpu_percent != null) m.push(s.cpu_percent + " % CPU");
            }
            if (s.heartbeat_age_s != null) m.push("dernière activité il y a " + fmtDur(s.heartbeat_age_s));
            m.push("redémarrages : " + s.restarts);
            if (s.errors_last_hour) m.push(s.errors_last_hour + " erreur(s)/h");
            it.appendChild(mk("div", "svc-meta", m.join(" · ")));
            if (s.last_exit) it.appendChild(mk("div", "svc-meta", "Dernière sortie : " + s.last_exit));
            if (s.last_action) it.appendChild(mk("div", "svc-meta", "Dernière action : " + s.last_action + " (" + s.last_action_by + ")"));
            if (s.last_error) it.appendChild(mk("div", "svc-err", (s.last_error.time || "") + " " + s.last_error.message));
            var ac = mk("div", "svc-actions"), lock = !!s.pending_action || sending;
            [["start", "Démarrer", "btn-primary", !s.running], ["restart", "Relancer", "btn-secondary", true],
             ["stop", "Arrêter", "btn-danger", s.running]].forEach(function (a) {
                var b = mk("button", "btn btn-sm " + a[2], a[1]); b.type = "button"; b.disabled = !a[3] || lock;
                b.onclick = function () { act(s.id, a[0]); }; ac.appendChild(b);
            });
            var lb = mk("button", "btn btn-sm btn-secondary", "Journal"); lb.type = "button";
            lb.onclick = function () { openLogs(s.id, s.label); }; ac.appendChild(lb);
            it.appendChild(ac); box.appendChild(it);
        });
    }
    function load() {
        /* watch=1 : prévient le dashboard qu'un admin regarde => l'agent appelle toutes les ~4 s */
        fetch("/api/services/status?watch=1").then(function (r) { return r.json(); }).then(render)
            .catch(function () { render({reachable: false, error: "Dashboard injoignable."}); });
    }
    function fetchLogs() {
        fetch("/admin/services/" + encodeURIComponent(logId) + "/logs?lines=150").then(function (r) { return r.json(); }).then(function (j) {
            var b = document.getElementById("logBox2"), atEnd = b.scrollHeight - b.clientHeight <= b.scrollTop + 50;
            b.textContent = "";
            (j.lines && j.lines.length ? j.lines : [j.error || "—"]).forEach(function (l) { b.appendChild(mk("div", null, l)); });
            if (atEnd) b.scrollTop = b.scrollHeight;
        }).catch(function () {});
    }
    function openLogs(id, label) {
        logId = id; document.getElementById("logTitle").textContent = "Journal — " + label;
        document.getElementById("logPanel").hidden = false; fetchLogs();
        clearInterval(logTimer); logTimer = setInterval(fetchLogs, 4000);
        document.getElementById("logBox2").scrollTop = 1e9;
    }
    function closeLogs() { document.getElementById("logPanel").hidden = true; clearInterval(logTimer); }
    load(); setInterval(function () { if (!sending) load(); }, 4000);
</script>
"""

ADMIN_SERVICES_HTML = _page("Scripts continus - Administration", _admin_head("Scripts continus") + r"""
  <section class="card">
    <div class="flex-row" style="margin-bottom:18px;">
        <h3 style="margin:0;">Serveur distant</h3>
        <span class="small muted" id="svcStamp"></span>
    </div>
    <div id="svcAdminList"></div>
  </section>

  <section class="card" id="logPanel" hidden>
    <div class="flex-row" style="margin-bottom:16px;">
        <h3 style="margin:0;" id="logTitle">Journal</h3>
        <button class="btn btn-secondary btn-sm" type="button" onclick="closeLogs()">Fermer</button>
    </div>
    <div class="console-window" id="logBox2"></div>
  </section>
""", tab="admin", extra_head='<meta name="csrf-token" content="{{ csrf_token() }}">', extra_js=_SVC_ADMIN_JS)
