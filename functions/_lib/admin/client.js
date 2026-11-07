export const CLIENT_SOURCE = `
const TYPES = ["agent", "workflow", "data_source", "model", "evaluation", "service"];
const TYPE_LABEL = { agent: "Agent", workflow: "Workflow", data_source: "Data source", model: "Model", evaluation: "Evaluation", service: "Service" };
const TYPE_HINT = {
  agent: "A bot or assistant. Recording it here does not connect to it.",
  workflow: "A repeatable process. Recording it here does not run it.",
  data_source: "A dataset or feed.",
  model: "A model, including a fine-tuned model. Recording it here does not load weights.",
  evaluation: "An evaluation or grade. Recording it here does not run one.",
  service: "A site, API, or other service."
};
const STATUSES = ["proposed", "active", "paused", "retired", "unavailable"];
const RULE_STATUSES = ["draft", "active", "retired"];
const TYPE_COLOR = { agent: "#9b3b22", workflow: "#2d6a43", data_source: "#7d5f17", model: "#c9a24a", evaluation: "#5b5c5e", service: "#17181a" };

function h(tag, attrs) {
  const node = document.createElement(tag);
  const extra = attrs || {};
  Object.keys(extra).forEach(function (key) {
    const value = extra[key];
    if (key === "class") node.className = value;
    else if (key.slice(0, 2) === "on" && typeof value === "function") node.addEventListener(key.slice(2), value);
    else if (value != null && value !== false) node.setAttribute(key, value);
  });
  for (let i = 2; i < arguments.length; i++) append(node, arguments[i]);
  return node;
}
function append(node, child) {
  if (child == null || child === false) return;
  if (Array.isArray(child)) { child.forEach(function (item) { append(node, item); }); return; }
  node.append(child instanceof Node ? child : document.createTextNode(String(child)));
}
function pill(status) { return h("span", { class: "pill " + status }, status); }
function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
async function api(path, options) {
  const opt = options || {};
  const headers = { accept: "application/json", "x-moneybeast-admin": "1" };
  if (opt.body) headers["content-type"] = "application/json";
  const res = await fetch("/admin/api" + path, {
    method: opt.method || "GET",
    credentials: "same-origin",
    headers: headers,
    body: opt.body ? JSON.stringify(opt.body) : undefined
  });
  const data = await res.json().catch(function () { return {}; });
  if (!res.ok) {
    const error = new Error(data.message || "Request failed");
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}
function when(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
function route() {
  const parts = location.hash.replace(/^#\\/?/, "").split("/").filter(Boolean);
  return { name: parts[0] || "map", id: parts[1] ? decodeURIComponent(parts[1]) : "" };
}
function markNav(name) {
  document.querySelectorAll("[data-nav]").forEach(function (link) {
    const on = link.getAttribute("data-nav") === name;
    if (on) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
}
let state = { components: [], rules: [], storage: null, query: "", type: "all", status: "all" };

function banner(kind, text) { return h("p", { class: "banner " + (kind || ""), role: "status" }, text); }
function issues(error) {
  const list = error && error.data && error.data.issues;
  if (!list || !list.length) return null;
  return h("ul", { class: "missing" }, list.map(function (item) {
    return h("li", null, item.path + ": " + item.message);
  }));
}
function storagePanel() {
  return h("section", { class: "panel" },
    h("p", { class: "eyebrow" }, "Storage disconnected"),
    h("h2", null, "The registry database is not bound."),
    h("p", { class: "lead" }, "ADMIN_DB is missing, so components, rules, and the audit log cannot be loaded or saved. This is not an empty registry."),
    h("p", { class: "meta" }, state.storage && state.storage.message ? state.storage.message : "Bind a D1 database as ADMIN_DB, then redeploy.")
  );
}

async function loadLists() {
  try {
    const components = await api("/components");
    const rules = await api("/rules");
    state.components = components.components || [];
    state.rules = rules.rules || [];
    state.storage = null;
  } catch (error) {
    if (error.status === 503 && error.data && error.data.error === "storage_unconfigured") {
      state.storage = error.data;
      state.components = [];
      state.rules = [];
      return;
    }
    throw error;
  }
}

function draw() {
  const view = route();
  markNav(view.name === "component" || view.name === "new" ? "registry" : (view.name === "rule" || view.name === "new-rule" ? "rules" : view.name));
  const app = document.getElementById("app");
  clear(app);
  const run = view.name === "rules" ? showRules
    : view.name === "rule" ? function () { return showRule(view.id); }
    : view.name === "new-rule" ? function () { return showRuleForm(null); }
    : view.name === "registry" ? showRegistry
    : view.name === "component" ? function () { return showComponent(view.id); }
    : view.name === "new" ? function () { return showComponentForm(null); }
    : view.name === "metrics" ? showMetrics
    : view.name === "audit" ? showAudit
    : showMap;
  Promise.resolve(run()).catch(function (error) {
    clear(app);
    app.append(banner("bad", error.message || "Something went wrong."));
  });
}

function showMap() {
  const app = document.getElementById("app");
  app.append(
    h("p", { class: "eyebrow" }, "System"),
    h("h1", null, "What depends on ", h("em", null, "what.")),
    h("p", { class: "lead" }, "A line runs from a dependency to the component that uses it. The first registry only lists what this repository actually publishes.")
  );
  if (state.storage) { app.append(storagePanel()); return; }
  const search = h("input", { type: "search", placeholder: "Highlight a component", "aria-label": "Highlight a component", value: state.query, oninput: function (event) {
    state.query = event.target.value;
    paint();
  }});
  app.append(h("div", { class: "tools" }, search));
  const wrap = h("div", { class: "graph-wrap" });
  const legend = h("div", { class: "legend" });
  TYPES.forEach(function (type) {
    legend.append(h("span", null, h("i", { class: "swatch", style: "background:" + TYPE_COLOR[type] }), TYPE_LABEL[type]));
  });
  app.append(wrap, legend);
  function paint() {
    clear(wrap);
    wrap.append(renderGraph(state.components, state.query.trim().toLowerCase()));
  }
  paint();
}

function ranksOf(components) {
  const byId = {};
  components.forEach(function (item) { byId[item.id] = item; });
  const memo = {};
  function rank(id, trail) {
    if (Object.prototype.hasOwnProperty.call(memo, id)) return memo[id];
    if (trail[id]) return 0;
    trail[id] = true;
    const deps = (byId[id].dependencies || []).filter(function (dep) { return byId[dep]; });
    let value = 0;
    deps.forEach(function (dep) { value = Math.max(value, rank(dep, trail) + 1); });
    memo[id] = value;
    return value;
  }
  components.forEach(function (item) { rank(item.id, {}); });
  return memo;
}

function renderGraph(components, query) {
  if (!components.length) return h("p", { class: "empty" }, "No components are registered.");
  const memo = ranksOf(components);
  const cols = [];
  components.forEach(function (item) {
    const rank = memo[item.id] || 0;
    if (!cols[rank]) cols[rank] = [];
    cols[rank].push(item);
  });
  const colW = 250;
  const rowH = 92;
  const pad = 20;
  const height = Math.max.apply(null, cols.map(function (col) { return col.length; })) * rowH + pad * 2;
  const width = cols.length * colW + pad;
  const pos = {};
  cols.forEach(function (col, ci) {
    col.forEach(function (item, ri) {
      pos[item.id] = { x: pad + ci * colW, y: pad + ri * rowH, w: 210, h: 68 };
    });
  });
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "graph");
  svg.setAttribute("viewBox", "0 0 " + width + " " + height);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Component dependency map");
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = '<marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6" fill="#7d5f17"></path></marker>';
  svg.append(defs);
  components.forEach(function (item) {
    (item.dependencies || []).forEach(function (dep) {
      if (!pos[dep] || !pos[item.id]) return;
      const a = pos[dep];
      const b = pos[item.id];
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const x1 = a.x + a.w;
      const y1 = a.y + a.h / 2;
      const x2 = b.x;
      const y2 = b.y + b.h / 2;
      const mid = (x1 + x2) / 2;
      path.setAttribute("d", "M" + x1 + " " + y1 + " C " + mid + " " + y1 + ", " + mid + " " + y2 + ", " + x2 + " " + y2);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "#c9a24a");
      path.setAttribute("stroke-width", "1.5");
      path.setAttribute("marker-end", "url(#arrow)");
      svg.append(path);
    });
  });
  components.forEach(function (item) {
    const box = pos[item.id];
    const hit = query && (item.name + " " + item.id + " " + item.owner + " " + item.purpose).toLowerCase().indexOf(query) === -1;
    const link = document.createElementNS("http://www.w3.org/2000/svg", "a");
    link.setAttribute("href", "#/component/" + encodeURIComponent(item.id));
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", box.x);
    rect.setAttribute("y", box.y);
    rect.setAttribute("width", box.w);
    rect.setAttribute("height", box.h);
    rect.setAttribute("rx", "14");
    rect.setAttribute("fill", "var(--card)");
    rect.setAttribute("stroke", TYPE_COLOR[item.type] || "#7d5f17");
    rect.setAttribute("stroke-width", "2");
    rect.setAttribute("opacity", hit ? "0.35" : "1");
    const title = document.createElementNS("http://www.w3.org/2000/svg", "text");
    title.setAttribute("x", box.x + 12);
    title.setAttribute("y", box.y + 28);
    title.setAttribute("fill", "var(--ink)");
    title.setAttribute("font-size", "15");
    title.setAttribute("font-family", "Georgia, serif");
    title.textContent = item.name.length > 26 ? item.name.slice(0, 25) + "…" : item.name;
    const sub = document.createElementNS("http://www.w3.org/2000/svg", "text");
    sub.setAttribute("x", box.x + 12);
    sub.setAttribute("y", box.y + 48);
    sub.setAttribute("fill", "var(--muted)");
    sub.setAttribute("font-size", "11");
    sub.setAttribute("font-family", "ui-monospace, monospace");
    sub.textContent = (TYPE_LABEL[item.type] || item.type) + " · " + item.status;
    link.append(rect, title, sub);
    svg.append(link);
  });
  return svg;
}

function showRegistry() {
  const app = document.getElementById("app");
  app.append(
    h("div", { class: "row" }, h("div", null, h("p", { class: "eyebrow" }, "Registry"), h("h1", null, "Components")), h("a", { class: "btn", href: "#/new" }, "New component"))
  );
  if (state.storage) { app.append(storagePanel()); return; }
  const search = h("input", { type: "search", "aria-label": "Search components", placeholder: "Search name, owner, purpose", value: state.query, oninput: function (event) { state.query = event.target.value; paint(); } });
  const status = h("select", { "aria-label": "Lifecycle", onchange: function (event) { state.status = event.target.value; paint(); } },
    h("option", { value: "all" }, "Any lifecycle"),
    STATUSES.map(function (item) { return h("option", { value: item, selected: state.status === item ? "selected" : null }, item); })
  );
  const chips = h("div", { class: "chips", role: "toolbar", "aria-label": "Component type" });
  ["all"].concat(TYPES).forEach(function (type) {
    chips.append(h("button", { type: "button", "aria-pressed": state.type === type ? "true" : "false", onclick: function () { state.type = type; paint(); } }, type === "all" ? "All" : TYPE_LABEL[type]));
  });
  const list = h("div", { class: "cards" });
  app.append(h("div", { class: "tools" }, search, status), chips, list);
  function paint() {
    clear(list);
    chips.querySelectorAll("button").forEach(function (button, index) {
      const type = ["all"].concat(TYPES)[index];
      button.setAttribute("aria-pressed", type === state.type ? "true" : "false");
    });
    const q = state.query.trim().toLowerCase();
    const rows = state.components.filter(function (item) {
      if (state.type !== "all" && item.type !== state.type) return false;
      if (state.status !== "all" && item.status !== state.status) return false;
      if (!q) return true;
      return (item.name + " " + item.id + " " + item.owner + " " + item.purpose + " " + item.provenance).toLowerCase().indexOf(q) !== -1;
    });
    if (!rows.length) {
      list.append(h("p", { class: "empty" }, state.components.length ? "Nothing matches those filters." : "The registry has no components."));
      return;
    }
    rows.forEach(function (item) {
      list.append(h("a", { class: "card", href: "#/component/" + encodeURIComponent(item.id) },
        h("div", { class: "row" }, h("b", null, item.name), pill(item.status)),
        h("span", { class: "meta" }, (TYPE_LABEL[item.type] || item.type) + (item.kind ? " · " + item.kind : "") + " · " + item.id),
        h("span", null, item.purpose),
        h("span", { class: "meta" }, "Owner " + item.owner + " · version " + item.version + " · updated " + when(item.updatedAt))
      ));
    });
  }
  paint();
}

async function showComponent(id) {
  const data = await api("/components/" + encodeURIComponent(id));
  const item = data.component;
  const app = document.getElementById("app");
  app.append(
    h("p", { class: "eyebrow" }, TYPE_LABEL[item.type] || item.type),
    h("h1", null, item.name),
    h("p", { class: "meta" }, pill(item.status), " ", "Revision " + item.revision + " · version " + item.version + " · updated " + when(item.updatedAt) + " by " + item.updatedBy)
  );
  const facts = h("dl", { class: "grid" });
  [["Owner", item.owner], ["Purpose", item.purpose], ["Provenance", item.provenance], ["Kind", item.kind || "—"], ["Effect", "Registry only. Runtime control: none."]].forEach(function (pair) {
    facts.append(h("div", null, h("dt", { class: "meta" }, pair[0]), h("dd", { style: "margin:0" }, pair[1])));
  });
  const deps = h("ul", null, (item.dependencies.length ? item.dependencies : ["None"]).map(function (dep) {
    return h("li", null, item.dependencies.length ? h("a", { href: "#/component/" + encodeURIComponent(dep) }, dep) : dep);
  }));
  const dependents = h("ul", null, (data.dependents.length ? data.dependents : [{ id: "", name: "None" }]).map(function (dep) {
    return h("li", null, dep.id ? h("a", { href: "#/component/" + encodeURIComponent(dep.id) }, dep.name) : dep.name);
  }));
  const rules = h("ul", null, (data.rules.length ? data.rules : [{ id: "", name: "No scoped rules" }]).map(function (rule) {
    return h("li", null, rule.id ? h("a", { href: "#/rule/" + encodeURIComponent(rule.id) }, rule.name) : rule.name);
  }));
  app.append(h("div", { class: "split" },
    h("section", { class: "panel" }, facts, h("h2", null, "Dependencies"), deps, h("h2", null, "Used by"), dependents),
    h("section", { class: "panel" }, h("h2", null, "Rules"), rules, h("p", { class: "meta" }, "Lifecycle is a label. Paused does not stop a bot or deploy."), h("a", { class: "btn", href: "#/component/" + encodeURIComponent(item.id) + "/edit" }, "Edit"))
  ));
  if (route().id && location.hash.indexOf("/edit") !== -1) showComponentForm(item);
}

function field(label, control) { return h("label", null, label, control); }
function input(name, value, attrs) {
  return h("input", Object.assign({ name: name, value: value || "" }, attrs || {}));
}
function select(name, options, current) {
  return h("select", { name: name }, options.map(function (option) {
    const value = option.value || option;
    const label = option.label || option;
    return h("option", { value: value, selected: value === current ? "selected" : null }, label);
  }));
}

function showComponentForm(existing) {
  const app = document.getElementById("app");
  if (!existing) {
    app.append(h("p", { class: "eyebrow" }, "Registry"), h("h1", null, "New component"));
  }
  if (state.storage) { app.append(storagePanel()); return; }
  const hint = h("p", { class: "meta" }, TYPE_HINT.service);
  const form = h("form", { class: "grid panel" });
  const type = select("type", TYPES.map(function (item) { return { value: item, label: TYPE_LABEL[item] }; }), existing ? existing.type : "service");
  type.addEventListener("change", function () { hint.textContent = TYPE_HINT[type.value] || ""; });
  hint.textContent = TYPE_HINT[type.value] || "";
  const box = h("div", { class: "checks" });
  state.components.filter(function (item) { return !existing || item.id !== existing.id; }).forEach(function (item) {
    const checked = existing && existing.dependencies.indexOf(item.id) !== -1;
    const checkbox = h("input", { type: "checkbox", name: "dep", value: item.id });
    if (checked) checkbox.checked = true;
    box.append(h("label", null, checkbox, item.name));
  });
  const note = h("div");
  form.append(
    field("Id", input("id", existing ? existing.id : "", { required: "required", pattern: "[a-z0-9][a-z0-9-]*", disabled: existing ? "disabled" : null })),
    field("Type", type),
    hint,
    field("Kind", input("kind", existing ? existing.kind : "", { placeholder: "optional, for example fine_tuned" })),
    field("Name", input("name", existing ? existing.name : "", { required: "required" })),
    field("Owner", input("owner", existing ? existing.owner : "Money Beast", { required: "required" })),
    field("Lifecycle", select("status", STATUSES, existing ? existing.status : "proposed")),
    h("p", { class: "meta" }, "Paused is only a registry label. It does not pause a bot, workflow, or the public site."),
    field("Version", input("version", existing ? existing.version : "1", { required: "required" })),
    field("Purpose", h("textarea", { name: "purpose", required: "required" }, existing ? existing.purpose : "")),
    field("Provenance", h("textarea", { name: "provenance", required: "required" }, existing ? existing.provenance : "")),
    field("Dependencies", box),
    note,
    h("div", { class: "tools" }, h("button", { class: "pri", type: "submit" }, "Save to registry"), existing ? h("button", { type: "button", class: "ghost", onclick: remove }, "Delete") : null)
  );
  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    clear(note);
    const deps = [];
    form.querySelectorAll("input[name=dep]:checked").forEach(function (box) { deps.push(box.value); });
    const body = {
      id: existing ? existing.id : form.elements.id.value.trim(),
      type: form.elements.type.value,
      kind: form.elements.kind.value.trim(),
      name: form.elements.name.value.trim(),
      owner: form.elements.owner.value.trim(),
      status: form.elements.status.value,
      version: form.elements.version.value.trim(),
      purpose: form.elements.purpose.value.trim(),
      provenance: form.elements.provenance.value.trim(),
      dependencies: deps
    };
    if (existing) body.expectedRevision = existing.revision;
    try {
      const saved = await api(existing ? "/components/" + encodeURIComponent(existing.id) : "/components", { method: existing ? "PATCH" : "POST", body: body });
      location.hash = "#/component/" + encodeURIComponent(saved.component.id);
      await loadLists();
      draw();
    } catch (error) {
      note.append(banner("bad", error.message), issues(error));
      if (error.status === 409 && error.data && error.data.current) {
        note.append(h("button", { type: "button", onclick: function () { showComponentForm(error.data.current); } }, "Load the current revision"));
      }
    }
  });
  async function remove() {
    if (!confirm("Delete this registry record? This does not change the public site or any runtime.")) return;
    try {
      await api("/components/" + encodeURIComponent(existing.id), { method: "DELETE", body: { expectedRevision: existing.revision } });
      location.hash = "#/registry";
      await loadLists();
      draw();
    } catch (error) {
      note.append(banner("bad", error.message), issues(error));
    }
  }
  if (existing) {
    const edit = document.getElementById("app");
    edit.append(h("section", null, h("h2", null, "Edit registry record"), form));
  } else app.append(form);
}

async function showRules() {
  const app = document.getElementById("app");
  app.append(h("div", { class: "row" }, h("div", null, h("p", { class: "eyebrow" }, "Policy"), h("h1", null, "Rules")), h("a", { class: "btn", href: "#/new-rule" }, "New rule")));
  if (state.storage) { app.append(storagePanel()); return; }
  if (!state.rules.length) { app.append(h("p", { class: "empty" }, "No rules are registered.")); return; }
  const list = h("div", { class: "cards" });
  state.rules.forEach(function (rule) {
    list.append(h("a", { class: "card", href: "#/rule/" + encodeURIComponent(rule.id) },
      h("div", { class: "row" }, h("b", null, rule.name), pill(rule.status)),
      h("span", { class: "meta" }, rule.scope + " · version " + rule.version + " · revision " + rule.revision),
      h("span", null, rule.statement),
      h("span", { class: "meta" }, "Affects " + (rule.resolvedAffected || []).length + " components · updated " + when(rule.updatedAt))
    ));
  });
  app.append(h("p", { class: "meta" }, "A saved rule is a registry policy. It is not pushed to a bot or to the public site."), list);
}

async function showRule(id) {
  const data = await api("/rules/" + encodeURIComponent(id));
  const rule = data.rule;
  const app = document.getElementById("app");
  app.append(
    h("p", { class: "eyebrow" }, "Rule · version " + rule.version),
    h("h1", null, rule.name),
    h("p", { class: "meta" }, pill(rule.status), " Scope " + rule.scope + " · revision " + rule.revision + " · updated " + when(rule.updatedAt) + " by " + rule.updatedBy),
    h("section", { class: "panel" }, h("p", null, rule.statement), h("p", { class: "meta" }, "Resolved components: " + ((rule.resolvedAffected || []).join(", ") || "none")))
  );
  const history = h("div", { class: "versions" });
  (data.versions || []).slice().reverse().forEach(function (version) {
    history.append(h("details", null,
      h("summary", null, "Version " + version.version + " · " + when(version.createdAt) + " · " + version.createdBy),
      h("p", null, version.snapshot.statement || "")
    ));
  });
  app.append(h("section", null, h("h2", null, "Versions"), history));
  showRuleForm(rule);
}

function showRuleForm(existing) {
  const app = document.getElementById("app");
  if (!existing) app.append(h("p", { class: "eyebrow" }, "Policy"), h("h1", null, "New rule"));
  if (state.storage) { app.append(storagePanel()); return; }
  const scopeOptions = [{ value: "global", label: "Global" }].concat(TYPES.map(function (type) {
    return { value: "type:" + type, label: "All " + TYPE_LABEL[type].toLowerCase() + "s" };
  })).concat(state.components.map(function (item) {
    return { value: "component:" + item.id, label: item.name };
  }));
  const form = h("form", { class: "grid panel" });
  const affected = h("div", { class: "checks" });
  state.components.forEach(function (item) {
    const checkbox = h("input", { type: "checkbox", name: "affected", value: item.id });
    if (existing && existing.affected.indexOf(item.id) !== -1) checkbox.checked = true;
    affected.append(h("label", null, checkbox, item.name));
  });
  const note = h("div");
  form.append(
    field("Id", input("id", existing ? existing.id : "", { required: "required", disabled: existing ? "disabled" : null })),
    field("Name", input("name", existing ? existing.name : "", { required: "required" })),
    field("Scope", select("scope", scopeOptions, existing ? existing.scope : "global")),
    field("Status", select("status", RULE_STATUSES, existing ? existing.status : "draft")),
    field("Statement", h("textarea", { name: "statement", required: "required" }, existing ? existing.statement : "")),
    field("Also affects", affected),
    h("p", { class: "meta" }, "Saving writes a new registry version. It does not change live prompts, routines, or the public site."),
    note,
    h("div", { class: "tools" }, h("button", { class: "pri", type: "submit" }, "Save rule"), existing ? h("button", { type: "button", onclick: remove }, "Delete") : null)
  );
  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    clear(note);
    const ids = [];
    form.querySelectorAll("input[name=affected]:checked").forEach(function (box) { ids.push(box.value); });
    const body = {
      id: existing ? existing.id : form.elements.id.value.trim(),
      name: form.elements.name.value.trim(),
      scope: form.elements.scope.value,
      status: form.elements.status.value,
      statement: form.elements.statement.value.trim(),
      affected: ids
    };
    if (existing) body.expectedRevision = existing.revision;
    try {
      const saved = await api(existing ? "/rules/" + encodeURIComponent(existing.id) : "/rules", { method: existing ? "PATCH" : "POST", body: body });
      location.hash = "#/rule/" + encodeURIComponent(saved.rule.id);
      await loadLists();
      draw();
    } catch (error) {
      note.append(banner("bad", error.message), issues(error));
      if (error.status === 409 && error.data && error.data.current) {
        note.append(h("button", { type: "button", onclick: async function () {
          const fresh = await api("/rules/" + encodeURIComponent(error.data.current.id));
          location.hash = "#/rule/" + encodeURIComponent(fresh.rule.id);
          draw();
        }}, "Reload current rule"));
      }
    }
  });
  async function remove() {
    if (!confirm("Delete this registry rule? This does not change a runtime.")) return;
    await api("/rules/" + encodeURIComponent(existing.id), { method: "DELETE", body: { expectedRevision: existing.revision } });
    location.hash = "#/rules";
    await loadLists();
    draw();
  }
  app.append(existing ? h("section", null, h("h2", null, "Edit rule"), form) : form);
}

async function showMetrics() {
  const data = await api("/metrics");
  const app = document.getElementById("app");
  app.append(
    h("p", { class: "eyebrow" }, "Metrics"),
    h("h1", null, "What we can ", h("em", null, "actually"), " see."),
    h("p", { class: "lead" }, data.note),
    h("p", { class: "meta" }, "Generated " + when(data.generatedAt) + ". " + (data.manifestNote || ""))
  );
  const grid = h("div", { class: "metrics" });
  (data.sources || []).forEach(function (source) {
    const lines = [
      h("div", { class: "row" }, h("b", null, source.label), pill(source.status)),
      h("p", { class: "meta" }, source.provenance || "")
    ];
    if (source.checkedAt) {
      const age = source.ageDays == null ? "" : " · " + Math.max(0, source.ageDays) + (source.ageDays === 1 ? " day old" : " days old");
      lines.push(h("p", null, "Checked " + source.checkedAt + age));
    }
    if (source.reason) lines.push(h("p", null, source.reason));
    if (source.counts) {
      const bits = TYPES.map(function (type) { return TYPE_LABEL[type] + " " + (source.counts.byType[type] || 0); }).join(" · ");
      const ruleCount = source.counts.rules;
      lines.push(h("p", null, source.counts.components + " components · " + ruleCount + (ruleCount === 1 ? " rule" : " rules")));
      lines.push(h("p", { class: "meta" }, bits));
      lines.push(h("p", { class: "meta" }, "Last audit " + when(source.counts.lastAuditAt)));
    }
    lines.push(h("p", { class: "meta" }, "No chart history."));
    grid.append(h("article", { class: "metric" }, lines));
  });
  app.append(grid);
}

async function showAudit() {
  const app = document.getElementById("app");
  app.append(h("p", { class: "eyebrow" }, "Audit"), h("h1", null, "Who changed the registry."));
  if (state.storage) { app.append(storagePanel()); return; }
  const data = await api("/audit?limit=50");
  if (!data.entries.length) { app.append(h("p", { class: "empty" }, "No audit entries.")); return; }
  const body = h("tbody");
  data.entries.forEach(function (entry) {
    body.append(h("tr", null,
      h("td", null, when(entry.at)),
      h("td", null, entry.actor),
      h("td", null, entry.action),
      h("td", null, entry.entityType + " " + entry.entityId),
      h("td", null, (entry.fromRevision == null ? "—" : String(entry.fromRevision)) + " → " + (entry.toRevision == null ? "—" : String(entry.toRevision))),
      h("td", null, entry.summary)
    ));
  });
  app.append(h("p", { class: "meta" }, data.provenance), h("div", { style: "overflow:auto" }, h("table", null,
    h("thead", null, h("tr", null, ["When", "Actor", "Action", "Record", "Revision", "Summary"].map(function (label) { return h("th", null, label); }))),
    body
  )));
}

document.getElementById("signout").addEventListener("click", async function () {
  await fetch("/admin/auth/logout", { method: "POST", credentials: "same-origin", headers: { "x-moneybeast-admin": "1", "content-type": "application/json" }, body: "{}" });
  location.href = "/admin";
});
addEventListener("hashchange", draw);
api("/session").then(function (session) {
  document.getElementById("who").textContent = "Google · " + session.email;
  return loadLists();
}).then(draw).catch(function (error) {
  const app = document.getElementById("app");
  clear(app);
  app.append(banner("bad", error.message || "Could not open the admin session."));
});
`;
