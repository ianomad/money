import { b64urlEncode } from "../../functions/_lib/admin/codec.js";
import { handleAdminRequest } from "../../functions/_lib/admin/handlers.js";
import { signSession } from "../../functions/_lib/admin/google.js";
import { createMemoryStore } from "../../functions/_lib/admin/store_memory.js";
import { createD1Store } from "../../functions/_lib/admin/store_d1.js";
import { createSqliteD1 } from "./sqlite_d1.js";

export const SECRET = "test-session-secret-should-be-32b-min";
export const ADMIN = "admin@example.com";
export const NOW = Date.parse("2026-11-07T12:00:00.000Z");

export function testEnv(extra = {}) {
  return {
    GOOGLE_CLIENT_ID: "test-client-id.apps.googleusercontent.com",
    GOOGLE_CLIENT_SECRET: "test-client-secret-value",
    ADMIN_SESSION_SECRET: SECRET,
    ADMIN_EMAILS: ADMIN,
    ...extra,
  };
}

export function createStore(kind) {
  if (kind === "memory") return createMemoryStore();
  if (kind === "d1") return createD1Store(createSqliteD1());
  throw new Error(kind);
}

export async function adminFetch(url, { env = testEnv(), store, session, method = "GET", body, headers = {}, now = NOW } = {}) {
  const requestHeaders = new Headers(headers);
  if (session) requestHeaders.set("cookie", "mb_admin_session=" + session);
  if (body != null && !requestHeaders.has("content-type")) requestHeaders.set("content-type", "application/json");
  if (method !== "GET" && method !== "HEAD") {
    requestHeaders.set("x-moneybeast-admin", "1");
    requestHeaders.set("origin", new URL(url).origin);
  }
  const request = new Request(url, {
    method,
    headers: requestHeaders,
    body: body == null ? undefined : (typeof body === "string" ? body : JSON.stringify(body)),
  });
  return handleAdminRequest(request, env, {
    store,
    now: () => now,
    fetch: async () => {
      throw new Error("unexpected network");
    },
  });
}

export async function signIn(env = testEnv()) {
  return signSession(env.ADMIN_SESSION_SECRET, { email: ADMIN, sub: "google-sub-1" }, NOW);
}

export async function rsa() {
  const pair = await crypto.subtle.generateKey(
    { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
    true,
    ["sign", "verify"],
  );
  const jwk = await crypto.subtle.exportKey("jwk", pair.publicKey);
  jwk.kid = "test-key";
  jwk.alg = "RS256";
  jwk.use = "sig";
  return { privateKey: pair.privateKey, jwks: { keys: [jwk] } };
}

export async function idToken(privateKey, payload, { alg = "RS256", kid = "test-key" } = {}) {
  const header = b64urlEncode(new TextEncoder().encode(JSON.stringify({ alg, kid, typ: "JWT" })));
  const body = b64urlEncode(new TextEncoder().encode(JSON.stringify(payload)));
  const data = header + "." + body;
  if (alg === "none") return data + ".";
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", privateKey, new TextEncoder().encode(data));
  return data + "." + b64urlEncode(new Uint8Array(sig));
}

export function cookieValue(response, name) {
  const cookies = response.headers.getSetCookie ? response.headers.getSetCookie() : [];
  const match = cookies.find((cookie) => cookie.startsWith(name + "="));
  if (!match) return null;
  return decodeURIComponent(match.slice(name.length + 1).split(";")[0]);
}

