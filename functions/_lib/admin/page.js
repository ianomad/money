function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

const CSS = `
:root {
  --paper:#fbfaf6; --card:#fff; --sunk:#f4f1e8; --ink:#17181a; --muted:#5b5c5e;
  --line:#e4dfd2; --gold:#7d5f17; --gold-2:#c9a24a; --gold-soft:#f3ebd6;
  --green:#2d6a43; --green-soft:#e5efe7; --red:#9b3b22; --red-soft:#f6e5df;
  --serif:"Iowan Old Style",Palatino,"Palatino Linotype",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  color-scheme:light dark;
}
@media (prefers-color-scheme:dark) {
  :root {
    --paper:#141311; --card:#1c1b18; --sunk:#22201c; --ink:#f1ede3; --muted:#b3ada0;
    --line:#34312a; --gold:#dcb760; --gold-2:#e9cf8a; --gold-soft:#2c2617;
    --green:#7cc394; --green-soft:#1b2a20; --red:#ee9a80; --red-soft:#33201a;
  }
}
* { box-sizing:border-box; }
html { scroll-padding-top:88px; }
body { margin:0; background:var(--paper); color:var(--ink); font:16px/1.5 var(--sans); }
a { color:var(--gold); }
:focus-visible { outline:2px solid var(--gold); outline-offset:2px; }
button, input, select, textarea { font:inherit; color:inherit; }
button { cursor:pointer; }
img { display:block; }
.skip { position:absolute; left:-999px; top:8px; background:var(--ink); color:var(--paper); padding:8px 12px; border-radius:8px; }
.skip:focus { left:8px; z-index:5; }
.top { position:sticky; top:0; z-index:4; background:color-mix(in srgb, var(--paper) 92%, transparent); backdrop-filter:blur(8px); border-bottom:1px solid var(--line); }
.bar, .wrap { max-width:1100px; margin:0 auto; padding-left:max(16px, env(safe-area-inset-left)); padding-right:max(16px, env(safe-area-inset-right)); }
.bar { min-height:64px; display:flex; align-items:center; gap:12px; }
.brand { display:flex; align-items:center; gap:10px; color:var(--ink); text-decoration:none; font:600 20px/1 var(--serif); }
.brand img { width:32px; height:32px; border-radius:8px; }
.brand b { color:var(--gold); font-weight:600; }
.who { margin-left:auto; font:12px var(--mono); color:var(--muted); }
.out { border:1px solid var(--line); background:var(--card); border-radius:999px; min-height:40px; padding:0 14px; }
.boundary { margin:0; padding:10px 0; color:var(--muted); font-size:14px; border-bottom:1px solid var(--line); }
.nav { display:flex; gap:6px; flex-wrap:wrap; padding:12px 0; }
.nav a, .btn, .ghost { display:inline-flex; align-items:center; justify-content:center; min-height:44px; padding:0 14px; border-radius:999px; text-decoration:none; border:1px solid var(--line); background:var(--card); color:var(--ink); font-weight:650; }
.nav a[aria-current=page] { background:var(--ink); color:var(--paper); border-color:var(--ink); }
.btn.pri, a.btn { background:var(--ink); color:var(--paper); border-color:var(--ink); }
.wrap { padding-top:8px; padding-bottom:96px; }
.eyebrow { font:650 12px/1.4 var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--gold); margin:0 0 8px; }
h1 { font:500 clamp(32px, 6vw, 48px)/1.08 var(--serif); letter-spacing:-.02em; margin:0 0 8px; }
h1 em, h2 em { color:var(--gold); font-style:italic; }
h2 { font:500 28px/1.2 var(--serif); margin:0; }
.lead { color:var(--muted); max-width:62ch; margin:0 0 16px; }
.gate { max-width:640px; margin:48px auto; padding:0 16px 48px; }
.notice, .banner { border-radius:14px; padding:12px 14px; margin:0 0 16px; background:var(--gold-soft); }
.banner.bad { background:var(--red-soft); color:var(--red); }
.banner.ok { background:var(--green-soft); }
.missing { margin:0; padding:0; list-style:none; display:grid; gap:8px; }
.missing li { font:14px var(--mono); background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px 12px; }
.tools { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:0 0 14px; }
.tools input, .tools select, .grid input, .grid select, .grid textarea { background:var(--card); border:1px solid var(--line); border-radius:12px; min-height:44px; padding:8px 12px; }
.tools input[type=search] { flex:1 1 220px; }
.chips { display:flex; gap:6px; flex-wrap:wrap; }
.chips button { min-height:36px; border-radius:999px; border:1px solid var(--line); background:var(--card); padding:0 12px; }
.chips button[aria-pressed=true] { background:var(--gold-soft); border-color:var(--gold); }
.cards { display:grid; gap:10px; }
.card, .metric, .panel { background:var(--card); border:1px solid var(--line); border-radius:16px; padding:14px 16px; }
.card { display:grid; gap:4px; color:inherit; text-decoration:none; }
.card:hover, .metric:hover { border-color:var(--gold); }
.card b { font-size:17px; }
.meta { color:var(--muted); font-size:13px; }
.pill { display:inline-flex; align-items:center; min-height:22px; padding:0 8px; border-radius:999px; font:650 11px var(--sans); background:var(--sunk); color:var(--muted); }
.pill.ok, .pill.active { background:var(--green-soft); color:var(--green); }
.pill.stale, .pill.paused, .pill.draft { background:var(--gold-soft); color:var(--gold); }
.pill.unavailable, .pill.disconnected, .pill.retired, .pill.bad { background:var(--red-soft); color:var(--red); }
.row { display:flex; justify-content:space-between; gap:12px; align-items:start; }
.metrics { display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:10px; }
.graph-wrap { overflow:auto; background:var(--card); border:1px solid var(--line); border-radius:16px; }
svg.graph { min-width:720px; width:100%; height:auto; display:block; }
.legend { display:flex; gap:10px; flex-wrap:wrap; margin:8px 0 0; font-size:13px; color:var(--muted); }
.swatch { width:10px; height:10px; border-radius:3px; display:inline-block; margin-right:6px; }
.grid { display:grid; gap:10px; }
.grid label { display:grid; gap:4px; font-size:13px; font-weight:650; color:var(--muted); }
.grid textarea { min-height:96px; resize:vertical; }
.checks { display:flex; flex-wrap:wrap; gap:8px; }
.checks label { display:flex; gap:8px; align-items:center; min-height:44px; padding:0 10px; border:1px solid var(--line); border-radius:999px; background:var(--paper); color:var(--ink); font-weight:600; }
.split { display:grid; gap:16px; }
@media (min-width:860px) { .split { grid-template-columns:1.2fr .8fr; align-items:start; } }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:8px 6px; border-bottom:1px solid var(--line); vertical-align:top; }
th { font:650 11px var(--mono); letter-spacing:.05em; text-transform:uppercase; color:var(--muted); }
.versions { display:grid; gap:8px; margin-top:8px; }
.versions details { border:1px solid var(--line); border-radius:12px; padding:8px 12px; background:var(--sunk); }
.versions summary { min-height:44px; display:flex; align-items:center; cursor:pointer; }
.empty { padding:28px 16px; text-align:center; color:var(--muted); border:1px dashed var(--line); border-radius:16px; }
.foot { margin-top:28px; color:var(--muted); font-size:13px; }
@media (max-width:720px) {
  .who { display:none; }
  .dock { position:fixed; left:0; right:0; bottom:0; display:grid; grid-template-columns:repeat(5, 1fr); gap:2px; background:var(--paper); border-top:1px solid var(--line); padding:4px 6px calc(4px + env(safe-area-inset-bottom)); z-index:6; }
  .dock a { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:48px; border-radius:12px; text-decoration:none; color:var(--muted); font:600 11px/1.1 var(--sans); }
  .dock a[aria-current=page] { background:var(--gold-soft); color:var(--ink); }
  .nav { display:none; }
}
@media (min-width:721px) { .dock { display:none; } }
@media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; } }
`;

function documentPage({ title, body, script = "" }) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><meta name="theme-color" content="#fbfaf6"><title>${escapeHtml(title)}</title><link rel="icon" href="/favicon.svg"><style>${CSS}</style></head><body>${body}${script ? `<script>${script}</script>` : ""}</body></html>`;
}

function brand() {
  return `<a class="brand" href="/"><img src="/favicon.svg" width="32" height="32" alt=""><span>Money <b>Beast</b></span></a>`;
}

export function renderUnconfigured(missing) {
  const items = missing.map((name) => `<li><code>${escapeHtml(name)}</code></li>`).join("");
  return documentPage({
    title: "Admin is not configured",
    body: `<main class="gate"><p class="eyebrow">Money Beast admin</p><h1>Google sign-in is not configured.</h1><p class="lead">The dashboard stays closed until the Pages project has a Google OAuth client, a session secret, and the admin allowlist. No registry data is available.</p><ul class="missing">${items}</ul></main>`,
  });
}

export function renderSignedOut(notice) {
  const banner = notice ? `<p class="notice" role="status">${escapeHtml(notice)}</p>` : "";
  return documentPage({
    title: "Sign in to Money Beast admin",
    body: `<main class="gate"><p class="eyebrow">Money Beast admin</p><h1>Sign in with <em>Google</em>.</h1><p class="lead">Only a verified Google account on the server allowlist can open the registry. Email codes, passwords, and unsigned headers are not accepted.</p>${banner}<a class="btn" href="/admin/auth/start">Continue with Google</a></main>`,
  });
}

export function renderMessage({ title, message }) {
  return documentPage({
    title,
    body: `<main class="gate"><p class="eyebrow">Money Beast admin</p><h1>${escapeHtml(title)}</h1><p class="lead">${escapeHtml(message)}</p></main>`,
  });
}

export function renderApp(script) {
  const links = [
    ["map", "Map"],
    ["registry", "Registry"],
    ["rules", "Rules"],
    ["metrics", "Metrics"],
    ["audit", "Audit"],
  ];
  const nav = links.map(([id, label]) => `<a href="#/${id}" data-nav="${id}">${label}</a>`).join("");
  return documentPage({
    title: "Money Beast admin",
    body: `<a class="skip" href="#app">Skip to content</a><header class="top"><div class="bar">${brand()}<span class="who" id="who">Google</span><button class="out" id="signout" type="button">Sign out</button></div><div class="wrap" style="padding-top:0;padding-bottom:0"><p class="boundary">Registry only. Saving here does not deploy the site, pause a bot, or change Grok Bot prompts or routines.</p><nav class="nav" aria-label="Admin">${nav}</nav></div></header><main class="wrap" id="app" tabindex="-1"><p class="lead">Loading the registry…</p></main><nav class="dock" aria-label="Admin">${nav}</nav>`,
    script,
  });
}
