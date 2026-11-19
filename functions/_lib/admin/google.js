import { b64urlDecode, randomToken, sha256B64url, signPayload, readSigned } from "./codec.js";

const text = new TextEncoder();
const decoder = new TextDecoder();
const GOOGLE_ISS = new Set(["https://accounts.google.com", "accounts.google.com"]);
const TOKEN_URL = "https://oauth2.googleapis.com/token";
const CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs";
const AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";

let certCache = { at: 0, jwks: null };

export function redirectUri(url) {
  return url.origin + "/admin/auth/callback";
}

export async function beginGoogleLogin(config, url, { secure, now = Date.now() }) {
  const state = randomToken(16);
  const nonce = randomToken(16);
  const verifier = randomToken(32);
  const challenge = await sha256B64url(verifier);
  const redirect = redirectUri(url);
  const token = await signPayload(config.sessionSecret, {
    v: 1,
    state,
    nonce,
    verifier,
    redirect,
    exp: now + 10 * 60 * 1000,
  });
  const auth = new URL(AUTH_URL);
  auth.searchParams.set("client_id", config.clientId);
  auth.searchParams.set("redirect_uri", redirect);
  auth.searchParams.set("response_type", "code");
  auth.searchParams.set("scope", "openid email");
  auth.searchParams.set("state", state);
  auth.searchParams.set("nonce", nonce);
  auth.searchParams.set("code_challenge", challenge);
  auth.searchParams.set("code_challenge_method", "S256");
  auth.searchParams.set("prompt", "select_account");
  return { location: auth.toString(), oauth: token, secure };
}

export async function completeGoogleLogin({ config, url, oauthToken, code, state, fetcher, now = Date.now(), cacheJwks = true }) {
  const saved = await readSigned(config.sessionSecret, oauthToken);
  if (!saved || saved.v !== 1 || saved.exp < now) return { error: "google_state" };
  if (!state || state !== saved.state) return { error: "google_state" };
  if (saved.redirect !== redirectUri(url)) return { error: "google_state" };
  if (!code) return { error: "google_denied" };

  const body = new URLSearchParams({
    code,
    client_id: config.clientId,
    client_secret: config.clientSecret,
    redirect_uri: saved.redirect,
    grant_type: "authorization_code",
    code_verifier: saved.verifier,
  });
  let tokenResponse;
  try {
    tokenResponse = await fetcher(TOKEN_URL, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded", accept: "application/json" },
      body,
      redirect: "manual",
    });
  } catch {
    return { error: "google_token" };
  }
  if (!tokenResponse || !tokenResponse.ok) return { error: "google_token" };
  let tokenJson;
  try {
    tokenJson = await tokenResponse.json();
  } catch {
    return { error: "google_token" };
  }
  if (!tokenJson || typeof tokenJson.id_token !== "string") return { error: "google_token" };

  let jwks = cacheJwks ? freshCache(now) : null;
  if (!jwks) {
    let certs;
    try {
      certs = await fetcher(CERTS_URL, { headers: { accept: "application/json" }, redirect: "manual" });
    } catch {
      return { error: "google_identity" };
    }
    if (!certs || !certs.ok) return { error: "google_identity" };
    try {
      jwks = await certs.json();
    } catch {
      return { error: "google_identity" };
    }
    if (cacheJwks) certCache = { at: now, jwks };
  }

  try {
    const identity = await verifyGoogleIdToken(tokenJson.id_token, {
      clientId: config.clientId,
      nonce: saved.nonce,
      jwks,
      now,
    });
    if (!config.emails.has(identity.email)) return { error: "not_allowlisted" };
    return { identity };
  } catch {
    return { error: "google_identity" };
  }
}

function freshCache(now) {
  if (!certCache.jwks || now - certCache.at > 10 * 60 * 1000) return null;
  return certCache.jwks;
}

export async function verifyGoogleIdToken(idToken, { clientId, nonce, jwks, now }) {
  const parts = String(idToken).split(".");
  if (parts.length !== 3) throw new Error("malformed");
  const header = JSON.parse(decoder.decode(b64urlDecode(parts[0])));
  const payload = JSON.parse(decoder.decode(b64urlDecode(parts[1])));
  if (header.alg !== "RS256" || !header.kid) throw new Error("alg");
  const jwk = (jwks.keys || []).find((key) => key.kid === header.kid && key.kty === "RSA");
  if (!jwk) throw new Error("kid");
  const key = await crypto.subtle.importKey(
    "jwk",
    { kty: "RSA", n: jwk.n, e: jwk.e, alg: "RS256", ext: true },
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const valid = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5",
    key,
    b64urlDecode(parts[2]),
    text.encode(parts[0] + "." + parts[1]),
  );
  if (!valid) throw new Error("sig");
  if (!GOOGLE_ISS.has(payload.iss)) throw new Error("iss");
  const aud = payload.aud;
  const audOk = aud === clientId || (Array.isArray(aud) && aud.includes(clientId));
  if (!audOk) throw new Error("aud");
  const skew = 60 * 1000;
  if (typeof payload.exp !== "number" || payload.exp * 1000 + skew < now) throw new Error("exp");
  if (typeof payload.iat === "number" && payload.iat * 1000 > now + skew) throw new Error("iat");
  if (!nonce || payload.nonce !== nonce) throw new Error("nonce");
  if (payload.email_verified !== true) throw new Error("email_verified");
  if (typeof payload.email !== "string" || typeof payload.sub !== "string" || !payload.sub) throw new Error("claims");
  return { email: payload.email.toLowerCase(), sub: payload.sub, provider: "google" };
}

export async function signSession(secret, identity, now = Date.now()) {
  return signPayload(secret, {
    v: 1,
    provider: "google",
    email: identity.email,
    sub: identity.sub,
    iat: now,
    exp: now + 8 * 60 * 60 * 1000,
  });
}

export async function readSession(secret, token, allow, now = Date.now()) {
  const payload = await readSigned(secret, token);
  if (!payload || payload.v !== 1 || payload.provider !== "google") return null;
  if (typeof payload.exp !== "number" || payload.exp < now) return null;
  if (typeof payload.email !== "string" || typeof payload.sub !== "string") return null;
  const email = payload.email.toLowerCase();
  if (!allow.has(email)) return null;
  return { email, sub: payload.sub, provider: "google", expiresAt: new Date(payload.exp).toISOString() };
}
