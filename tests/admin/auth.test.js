import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { readSigned } from "../../functions/_lib/admin/codec.js";
import { handleAdminRequest } from "../../functions/_lib/admin/handlers.js";
import { CLIENT_SOURCE } from "../../functions/_lib/admin/client.js";
import {
  ADMIN, NOW, SECRET, adminFetch, cookieValue, idToken, rsa, signIn, testEnv,
} from "./harness.js";

const ORIGIN = "https://getmoneybeast.com";

test("client script parses", () => {
  new Function(CLIENT_SOURCE);
});

test("missing Google configuration fails closed and does not echo secrets", async () => {
  const env = {
    GOOGLE_CLIENT_ID: "test-client-id.apps.googleusercontent.com",
    GOOGLE_CLIENT_SECRET: "super-secret-value-xyz",
    ADMIN_SESSION_SECRET: "short",
  };
  const page = await adminFetch(ORIGIN + "/admin", { env });
  const api = await adminFetch(ORIGIN + "/admin/api/components", { env });
  assert.equal(page.status, 503);
  assert.equal(api.status, 503);
  const html = await page.text();
  const json = await api.json();
  assert.match(html, /Google sign-in is not configured/);
  assert.match(html, /ADMIN_EMAILS/);
  assert.match(html, /ADMIN_SESSION_SECRET/);
  assert.equal(html.includes("super-secret-value-xyz"), false);
  assert.equal(html.includes("Continue with Google"), false);
  assert.equal(html.includes("editorial-datasets"), false);
  assert.deepEqual(json.missing.includes("ADMIN_EMAILS"), true);
  assert.equal(JSON.stringify(json).includes("super-secret-value-xyz"), false);
});

test("configured but signed out denies pages and APIs", async () => {
  const page = await adminFetch(ORIGIN + "/admin");
  const api = await adminFetch(ORIGIN + "/admin/api/metrics");
  assert.equal(page.status, 401);
  assert.equal(api.status, 401);
  const html = await page.text();
  assert.match(html, /Continue with Google/);
  assert.match(html, /verified Google account/);
  assert.equal(html.includes("editorial-datasets"), false);
  assert.equal((await api.json()).error, "unauthorized");
});

test("wrong host and plain http are denied", async () => {
  const host = await adminFetch("https://preview.example/admin");
  assert.equal(host.status, 403);
  const http = await adminFetch("http://getmoneybeast.com/admin");
  assert.equal(http.status, 400);
  const local = await handleAdminRequest(new Request("http://127.0.0.1/admin"), testEnv({ ADMIN_ALLOWED_HOSTS: "127.0.0.1" }), { now: () => NOW });
  assert.equal(local.status, 400);
});

test("Google login accepts only a verified allowlisted Google identity", async () => {
  const keys = await rsa();
  const env = testEnv();
  const start = await handleAdminRequest(new Request(ORIGIN + "/admin/auth/start"), env, { now: () => NOW });
  assert.equal(start.status, 302);
  const location = new URL(start.headers.get("location"));
  assert.equal(location.origin, "https://accounts.google.com");
  assert.equal(location.searchParams.get("scope"), "openid email");
  assert.equal(location.searchParams.get("redirect_uri"), ORIGIN + "/admin/auth/callback");
  const oauth = cookieValue(start, "mb_admin_oauth");
  const saved = await readSigned(SECRET, oauth);
  assert.equal(saved.state, location.searchParams.get("state"));
  assert.equal(start.headers.get("set-cookie").includes("HttpOnly"), true);
  assert.equal(start.headers.get("set-cookie").includes("Secure"), true);
  assert.equal(start.headers.get("set-cookie").includes("Path=/admin"), true);

  async function callback(payload) {
    const token = await idToken(keys.privateKey, {
      iss: "https://accounts.google.com",
      aud: env.GOOGLE_CLIENT_ID,
      exp: Math.floor(NOW / 1000) + 300,
      iat: Math.floor(NOW / 1000),
      nonce: saved.nonce,
      email_verified: true,
      email: ADMIN,
      sub: "google-sub-1",
      ...payload,
    });
    return handleAdminRequest(new Request(ORIGIN + "/admin/auth/callback?code=abc&state=" + saved.state, {
      headers: { cookie: "mb_admin_oauth=" + encodeURIComponent(oauth) },
    }), env, {
      now: () => NOW,
      fetch: async (url) => {
        if (String(url).includes("/token")) return Response.json({ id_token: token });
        if (String(url).includes("/certs")) return Response.json(keys.jwks);
        throw new Error("unexpected " + url);
      },
    });
  }

  const ok = await callback();
  assert.equal(ok.status, 302);
  assert.equal(ok.headers.get("location"), ORIGIN + "/admin");
  const session = cookieValue(ok, "mb_admin_session");
  assert.ok(session);
  const who = await adminFetch(ORIGIN + "/admin/api/session", { session });
  assert.equal(who.status, 200);
  assert.deepEqual(await who.json(), {
    schemaVersion: 1,
    email: ADMIN,
    provider: "google",
    expiresAt: new Date(NOW + 8 * 60 * 60 * 1000).toISOString(),
  });

  for (const [name, payload] of [
    ["other email", { email: "other@example.com" }],
    ["unverified", { email_verified: false }],
    ["string verified flag", { email_verified: "true" }],
    ["wrong issuer", { iss: "https://example.com" }],
    ["wrong audience", { aud: "another-client" }],
    ["expired", { exp: Math.floor(NOW / 1000) - 600 }],
    ["wrong nonce", { nonce: "nope" }],
  ]) {
    const denied = await callback(payload);
    assert.equal(denied.status, 302, name);
    assert.match(denied.headers.get("location"), /error=(not_allowlisted|google_identity)/, name);
    assert.equal(cookieValue(denied, "mb_admin_session"), "", name);
  }

  const none = await idToken(keys.privateKey, { alg: "none" }, { alg: "none" });
  const unsigned = await handleAdminRequest(new Request(ORIGIN + "/admin/auth/callback?code=abc&state=" + saved.state, {
    headers: { cookie: "mb_admin_oauth=" + encodeURIComponent(oauth) },
  }), env, {
    now: () => NOW,
    fetch: async (url) => String(url).includes("/token") ? Response.json({ id_token: none }) : Response.json(keys.jwks),
  });
  assert.match(unsigned.headers.get("location"), /google_identity/);
});

test("forged, expired, and de-allowlisted sessions are rejected", async () => {
  const session = await signIn();
  const forged = await adminFetch(ORIGIN + "/admin/api/components", { session: session + "tampered" });
  assert.equal(forged.status, 401);
  const emailHeader = await adminFetch(ORIGIN + "/admin/api/session", {
    headers: { "x-user-email": "attacker@example.com", cookie: "mb_admin_session=" + session },
  });
  assert.equal((await emailHeader.json()).email, ADMIN);
  const removed = await adminFetch(ORIGIN + "/admin/api/session", {
    env: testEnv({ ADMIN_EMAILS: "someone-else@example.com" }),
    session,
  });
  assert.equal(removed.status, 401);
  const stale = await adminFetch(ORIGIN + "/admin/api/session", { session, now: NOW + 9 * 60 * 60 * 1000 });
  assert.equal(stale.status, 401);
});

test("mutations require a same-origin admin header", async () => {
  const session = await signIn();
  const request = new Request(ORIGIN + "/admin/api/components", {
    method: "POST",
    headers: { cookie: "mb_admin_session=" + session, "content-type": "application/json", origin: "https://evil.example" },
    body: JSON.stringify({ id: "x" }),
  });
  const res = await handleAdminRequest(request, testEnv(), { now: () => NOW, store: (await import("../../functions/_lib/admin/store_memory.js")).createMemoryStore() });
  assert.equal(res.status, 403);
  assert.equal((await res.json()).error, "csrf");
});

test("production entry has no dev auth bypass", () => {
  const entry = readFileSync(new URL("../../functions/admin/[[path]].js", import.meta.url), "utf8");
  assert.match(entry, /handleAdminRequest\(context\.request, context\.env\)/);
  assert.doesNotMatch(entry, /allowInsecure|preview@|DEV_AUTH|bypass/i);
  const handlers = readFileSync(new URL("../../functions/_lib/admin/handlers.js", import.meta.url), "utf8");
  assert.doesNotMatch(handlers, /env\.allowInsecure|env\.DEV|ADMIN_PREVIEW|localStorage/i);
});

test("signed-in shell contains no seeded records", async () => {
  const session = await signIn();
  const page = await adminFetch(ORIGIN + "/admin", { session });
  assert.equal(page.status, 200);
  const html = await page.text();
  assert.match(html, /Registry only/);
  assert.match(html, /does not deploy the site/);
  assert.equal(html.includes("editorial-datasets"), false);
  assert.equal(html.includes(ADMIN), false);
});
