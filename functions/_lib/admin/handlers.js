import { readCookie, serializeCookie } from "./codec.js";
import { CANONICAL_HOST, readConfig, storageBinding } from "./config.js";
import { beginGoogleLogin, completeGoogleLogin, readSession, signSession } from "./google.js";
import { buildMetrics } from "./metrics.js";
import {
  JSON_SCHEMA,
  SCHEMA_VERSION,
  parseScope,
  presentComponent,
  presentRule,
  validateComponentInput,
  validateRuleInput,
} from "./schema.js";
import { createD1Store } from "./store_d1.js";
import { renderApp, renderMessage, renderSignedOut, renderUnconfigured } from "./page.js";
import { CLIENT_SOURCE } from "./client.js";

const SESSION = "mb_admin_session";
const OAUTH = "mb_admin_oauth";
const ERRORS = {
  not_allowlisted: "That Google account is not on the admin allowlist.",
  google_denied: "Google did not complete sign-in.",
  google_state: "The sign-in attempt expired or did not match this browser. Start again.",
  google_token: "Google did not return a usable sign-in.",
  google_identity: "The Google identity token was not accepted. Sign-in must be a verified Google account.",
};

function securityHeaders(init = {}) {
  const headers = new Headers(init);
  headers.set("cache-control", "no-store");
  headers.set("x-content-type-options", "nosniff");
  headers.set("referrer-policy", "no-referrer");
  headers.set("x-frame-options", "DENY");
  headers.set(
    "content-security-policy",
    "default-src 'self'; img-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
  );
  headers.set("x-robots-tag", "noindex, nofollow");
  return headers;
}

function html(body, status, cookies = [], secure = true) {
  const headers = securityHeaders({ "content-type": "text/html; charset=utf-8" });
  for (const cookie of cookies) headers.append("set-cookie", cookie);
  return new Response(body, { status, headers });
}

function json(data, status = 200, cookies = [], secure = true) {
  const headers = securityHeaders({ "content-type": "application/json; charset=utf-8" });
  for (const cookie of cookies) headers.append("set-cookie", cookie);
  return new Response(JSON.stringify(data), { status, headers });
}

function clearCookie(name, secure) {
  return serializeCookie(name, "", { maxAge: 0, secure });
}

function sessionCookie(value, secure) {
  return serializeCookie(SESSION, value, { maxAge: 8 * 60 * 60, secure });
}

function normalizePath(pathname) {
  if (pathname.length > 1 && pathname.endsWith("/")) return pathname.slice(0, -1);
  return pathname;
}

function wantsJson(url) {
  return url.pathname.startsWith("/admin/api/");
}

async function readBody(request) {
  const raw = await request.text();
  if (raw.length > 100000) return { error: "too_large" };
  if (!raw.trim()) return { value: {} };
  try {
    const value = JSON.parse(raw);
    if (!value || typeof value !== "object" || Array.isArray(value)) return { error: "invalid_json" };
    return { value };
  } catch {
    return { error: "invalid_json" };
  }
}

function csrfOk(request, url) {
  if (request.headers.get("x-moneybeast-admin") !== "1") return false;
  const origin = request.headers.get("origin");
  if (!origin) return false;
  try {
    return new URL(origin).host === url.host;
  } catch {
    return false;
  }
}

function resolvedAffected(rule, components) {
  const known = new Set(components.map((item) => item.id));
  const explicit = rule.affected.filter((id) => known.has(id));
  const scope = parseScope(rule.scope);
  let matched = [];
  if (scope?.kind === "global") matched = components.map((item) => item.id);
  else if (scope?.kind === "type") matched = components.filter((item) => item.type === scope.type).map((item) => item.id);
  else if (scope?.kind === "component" && known.has(scope.id)) matched = [scope.id];
  return [...new Set([...matched, ...explicit])];
}

function storeFor(env, deps) {
  if (deps.store) return deps.store;
  const binding = storageBinding(env);
  return binding ? createD1Store(binding) : null;
}

async function prepareStore(store, now) {
  if (!store) return null;
  await store.seedIfEmpty(now);
  return store;
}

function unknownDeps(ids, components, self) {
  const known = new Set(components.map((item) => item.id).filter((id) => id !== self));
  return ids.filter((id) => !known.has(id));
}

export async function handleAdminRequest(request, env = {}, deps = {}) {
  const url = new URL(request.url);
  const path = normalizePath(url.pathname);
  const nowMs = deps.now ? deps.now() : Date.now();
  const now = new Date(nowMs).toISOString();
  const secure = url.protocol === "https:";
  const localHttp = deps.allowInsecureLocalhost === true
    && url.protocol === "http:"
    && (url.hostname === "127.0.0.1" || url.hostname === "localhost");
  if (!secure && !localHttp) {
    return json({ error: "https_required", message: "Admin sign-in requires HTTPS." }, 400);
  }
  const cookieSecure = secure;

  const config = readConfig(env);
  const allowed = config.ok ? config.hosts : new Set([CANONICAL_HOST]);
  if (!allowed.has(url.hostname.toLowerCase())) {
    const message = "This host is not allowed to serve admin sign-in.";
    return wantsJson(url) ? json({ error: "host_not_allowed", message }, 403) : html(renderMessage({ title: "Host not allowed", message }), 403);
  }
  if (!config.ok) {
    const body = { error: "admin_unconfigured", message: "Google admin sign-in is not configured.", missing: config.missing };
    return wantsJson(url) ? json(body, 503) : html(renderUnconfigured(config.missing), 503);
  }

  const fetcher = deps.fetch || fetch;
  if (path === "/admin/auth/start" && request.method === "GET") {
    const started = await beginGoogleLogin(config, url, { secure: cookieSecure, now: nowMs });
    const headers = securityHeaders({ location: started.location });
    headers.append("set-cookie", serializeCookie(OAUTH, started.oauth, { maxAge: 600, secure: cookieSecure }));
    return new Response(null, { status: 302, headers });
  }
  if (path === "/admin/auth/callback" && request.method === "GET") {
    const result = await completeGoogleLogin({
      config,
      url,
      oauthToken: readCookie(request, OAUTH),
      code: url.searchParams.get("code"),
      state: url.searchParams.get("state"),
      fetcher,
      now: nowMs,
      cacheJwks: !deps.fetch,
    });
    const cleared = clearCookie(OAUTH, cookieSecure);
    if (result.error) {
      const headers = securityHeaders({ location: url.origin + "/admin?error=" + result.error });
      headers.append("set-cookie", cleared);
      headers.append("set-cookie", clearCookie(SESSION, cookieSecure));
      return new Response(null, { status: 302, headers });
    }
    const session = await signSession(config.sessionSecret, result.identity, nowMs);
    const headers = securityHeaders({ location: url.origin + "/admin" });
    headers.append("set-cookie", cleared);
    headers.append("set-cookie", sessionCookie(session, cookieSecure));
    return new Response(null, { status: 302, headers });
  }
  if (path === "/admin/auth/logout" && request.method === "POST") {
    if (!csrfOk(request, url)) return json({ error: "csrf", message: "The request was missing a same-origin admin header." }, 403);
    return json({ ok: true }, 200, [clearCookie(SESSION, cookieSecure), clearCookie(OAUTH, cookieSecure)]);
  }

  const session = await readSession(config.sessionSecret, readCookie(request, SESSION), config.emails, nowMs);
  if (!session) {
    if (wantsJson(url)) return json({ error: "unauthorized", message: "Sign in with Google is required." }, 401);
    if (path === "/admin") {
      const code = url.searchParams.get("error");
      const notice = Object.prototype.hasOwnProperty.call(ERRORS, code) ? ERRORS[code] : "";
      return html(renderSignedOut(notice), 401);
    }
    return html(renderMessage({ title: "Sign-in required", message: "Sign in with Google to open admin." }), 401);
  }

  if (path === "/admin" && request.method === "GET") return html(renderApp(CLIENT_SOURCE), 200);
  if (!path.startsWith("/admin/api/")) return html(renderMessage({ title: "Not found", message: "That admin page does not exist." }), 404);

  if (request.method !== "GET" && request.method !== "HEAD" && !csrfOk(request, url)) {
    return json({ error: "csrf", message: "The request was missing a same-origin admin header." }, 403);
  }

  const store = await prepareStore(storeFor(env, deps), now);
  const segments = path.slice("/admin/api/".length).split("/").map(decodeURIComponent);
  try {
    return await dispatch({ request, url, segments, session, store, now });
  } catch {
    return json({ error: "storage_error", message: "The admin registry could not be read or saved." }, 500);
  }
}

async function dispatch({ request, segments, session, store, now }) {
  const [group, id] = segments;
  if (group === "session" && !id && request.method === "GET") {
    return json({ schemaVersion: SCHEMA_VERSION, email: session.email, provider: "google", expiresAt: session.expiresAt });
  }
  if (group === "schema" && !id && request.method === "GET") return json(JSON_SCHEMA);
  if (group === "metrics" && !id && request.method === "GET") {
    const counts = store ? await store.counts() : null;
    return json(buildMetrics({ now, storage: Boolean(store), counts }));
  }
  if (!store) {
    return json({
      error: "storage_unconfigured",
      message: "The admin database binding ADMIN_DB is not configured. Registry data is unavailable.",
    }, 503);
  }
  if (group === "audit" && !id && request.method === "GET") {
    const limit = Math.min(100, Math.max(1, Number(new URL(request.url).searchParams.get("limit") || 50) || 50));
    const entries = await store.listAudit(limit);
    return json({ schemaVersion: SCHEMA_VERSION, provenance: "ADMIN_DB audit table", entries });
  }
  if (group === "components" && !id && request.method === "GET") {
    const components = (await store.listComponents()).map(presentComponent);
    return json({ schemaVersion: SCHEMA_VERSION, effect: "registry_only", components });
  }
  if (group === "components" && !id && request.method === "POST") return saveComponent(request, store, session, now, null);
  if (group === "components" && id && request.method === "GET") return getComponent(store, id);
  if (group === "components" && id && request.method === "PATCH") return saveComponent(request, store, session, now, id);
  if (group === "components" && id && request.method === "DELETE") return removeComponent(request, store, session, now, id);
  if (group === "rules" && !id && request.method === "GET") return listRules(store);
  if (group === "rules" && !id && request.method === "POST") return saveRule(request, store, session, now, null);
  if (group === "rules" && id && request.method === "GET") return getRule(store, id);
  if (group === "rules" && id && request.method === "PATCH") return saveRule(request, store, session, now, id);
  if (group === "rules" && id && request.method === "DELETE") return removeRule(request, store, session, now, id);
  return json({ error: "not_found", message: "That admin API does not exist." }, 404);
}

async function getComponent(store, id) {
  const row = await store.getComponent(id);
  if (!row) return json({ error: "not_found", message: "No component with that id." }, 404);
  const components = await store.listComponents();
  const rules = await store.listRules();
  const affecting = rules
    .filter((rule) => resolvedAffected(rule, components).includes(id))
    .map((rule) => ({ id: rule.id, name: rule.name, scope: rule.scope, status: rule.status, version: rule.version }));
  return json({
    component: presentComponent(row),
    dependents: await store.dependents(id),
    rules: affecting,
  });
}

async function saveComponent(request, store, session, now, existingId) {
  const body = await readBody(request);
  if (body.error) return json({ error: body.error, message: "The request body was not valid JSON." }, 400);
  const parsed = validateComponentInput(body.value, { requireRevision: Boolean(existingId) });
  if (!parsed.ok) return json({ error: "invalid", message: "The component did not validate.", issues: parsed.issues }, 400);
  if (existingId && parsed.value.id !== existingId) {
    return json({ error: "invalid", message: "The component id cannot change.", issues: [{ path: "id", message: "Id is permanent." }] }, 400);
  }
  const components = await store.listComponents();
  const missing = unknownDeps(parsed.value.dependencies, components, parsed.value.id);
  if (missing.length) {
    return json({ error: "invalid", message: "Every dependency must already be in the registry.", issues: [{ path: "dependencies", message: "Unknown: " + missing.join(", ") }] }, 400);
  }
  const fields = { ...parsed.value };
  delete fields.expectedRevision;
  const result = existingId
    ? await store.updateComponent(existingId, fields, parsed.value.expectedRevision, session.email, now)
    : await store.insertComponent(fields, session.email, now);
  return writeResult(result, "component", existingId ? 200 : 201);
}

async function removeComponent(request, store, session, now, id) {
  const body = await readBody(request);
  if (body.error) return json({ error: body.error, message: "The request body was not valid JSON." }, 400);
  const expected = body.value.expectedRevision;
  if (!Number.isInteger(expected) || expected < 1) {
    return json({ error: "invalid", message: "A revision is required.", issues: [{ path: "expectedRevision", message: "Required." }] }, 400);
  }
  const result = await store.deleteComponent(id, expected, session.email, now);
  if (result.inUse) {
    return json({
      error: "in_use",
      message: "Other registry records still reference this component.",
      dependents: result.dependents || [],
      rules: result.rules || [],
    }, 409);
  }
  return writeResult(result, "component", 200);
}

async function listRules(store) {
  const components = await store.listComponents();
  const rules = await store.listRules();
  return json({
    schemaVersion: SCHEMA_VERSION,
    effect: "registry_only",
    rules: rules.map((rule) => presentRule(rule, resolvedAffected(rule, components))),
  });
}

async function getRule(store, id) {
  const row = await store.getRule(id);
  if (!row) return json({ error: "not_found", message: "No rule with that id." }, 404);
  const components = await store.listComponents();
  const versions = await store.ruleVersions(id);
  return json({
    rule: presentRule(row, resolvedAffected(row, components)),
    versions: versions.map((version) => ({
      version: version.version,
      createdAt: version.createdAt,
      createdBy: version.createdBy,
      snapshot: version.snapshot,
    })),
  });
}

async function saveRule(request, store, session, now, existingId) {
  const body = await readBody(request);
  if (body.error) return json({ error: body.error, message: "The request body was not valid JSON." }, 400);
  const parsed = validateRuleInput(body.value, { requireRevision: Boolean(existingId) });
  if (!parsed.ok) return json({ error: "invalid", message: "The rule did not validate.", issues: parsed.issues }, 400);
  if (existingId && parsed.value.id !== existingId) {
    return json({ error: "invalid", message: "The rule id cannot change.", issues: [{ path: "id", message: "Id is permanent." }] }, 400);
  }
  const components = await store.listComponents();
  const known = new Set(components.map((item) => item.id));
  const scope = parseScope(parsed.value.scope);
  const issues = [];
  if (scope.kind === "component" && !known.has(scope.id)) issues.push({ path: "scope", message: "That component is not in the registry." });
  const missing = parsed.value.affected.filter((item) => !known.has(item));
  if (missing.length) issues.push({ path: "affected", message: "Unknown: " + missing.join(", ") });
  if (issues.length) return json({ error: "invalid", message: "The rule points at a component that is not registered.", issues }, 400);
  const fields = { ...parsed.value };
  delete fields.expectedRevision;
  const result = existingId
    ? await store.updateRule(existingId, fields, parsed.value.expectedRevision, session.email, now)
    : await store.insertRule(fields, session.email, now);
  if (result.record) {
    const fresh = await store.listComponents();
    result.record = presentRule(result.record, resolvedAffected(result.record, fresh));
    return json({ rule: result.record }, existingId ? 200 : 201);
  }
  return writeResult(result, "rule", existingId ? 200 : 201);
}

async function removeRule(request, store, session, now, id) {
  const body = await readBody(request);
  if (body.error) return json({ error: body.error, message: "The request body was not valid JSON." }, 400);
  const expected = body.value.expectedRevision;
  if (!Number.isInteger(expected) || expected < 1) {
    return json({ error: "invalid", message: "A revision is required.", issues: [{ path: "expectedRevision", message: "Required." }] }, 400);
  }
  return writeResult(await store.deleteRule(id, expected, session.email, now), "rule", 200);
}

function writeResult(result, key, status) {
  if (result.exists) return json({ error: "exists", message: "A record with that id already exists." }, 409);
  if (result.limit) return json({ error: "limit", message: "The registry has reached its limit of 200 records of this kind." }, 409);
  if (result.notFound) return json({ error: "not_found", message: "No record with that id." }, 404);
  if (result.conflict) {
    const current = key === "component" ? presentComponent(result.current) : presentRule(result.current, result.current.affected || []);
    return json({
      error: "revision_conflict",
      message: "This record changed after you loaded it. Review the current revision and save again.",
      current,
    }, 409);
  }
  if (result.deleted) return json({ ok: true });
  if (result.record) {
    const presented = key === "component" ? presentComponent(result.record) : result.record;
    return json({ [key]: presented }, status);
  }
  return json({ error: "storage_error", message: "The registry did not accept the change." }, 500);
}
