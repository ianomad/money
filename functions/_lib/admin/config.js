const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const HOST_RE = /^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?)+$/;

export const CANONICAL_HOST = "getmoneybeast.com";
export const REQUIRED_SETTINGS = [
  "GOOGLE_CLIENT_ID",
  "GOOGLE_CLIENT_SECRET",
  "ADMIN_SESSION_SECRET",
  "ADMIN_EMAILS",
];

function validHost(host) {
  return host === "localhost" || host === "127.0.0.1" || HOST_RE.test(host);
}

export function readConfig(env = {}) {
  const missing = [];
  const clientId = String(env.GOOGLE_CLIENT_ID || "").trim();
  const clientSecret = String(env.GOOGLE_CLIENT_SECRET || "").trim();
  const sessionSecret = String(env.ADMIN_SESSION_SECRET || "").trim();
  const emails = String(env.ADMIN_EMAILS || "")
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
  if (clientId.length < 10) missing.push("GOOGLE_CLIENT_ID");
  if (clientSecret.length < 10) missing.push("GOOGLE_CLIENT_SECRET");
  if (sessionSecret.length < 32) missing.push("ADMIN_SESSION_SECRET");
  if (!emails.length || emails.some((email) => !EMAIL_RE.test(email))) missing.push("ADMIN_EMAILS");

  const hosts = new Set([CANONICAL_HOST]);
  const extra = String(env.ADMIN_ALLOWED_HOSTS || "").trim();
  if (extra) {
    let hostsOk = true;
    for (const raw of extra.split(",")) {
      const host = raw.trim().toLowerCase();
      if (!host) continue;
      if (!validHost(host) || host.includes("*")) hostsOk = false;
      else hosts.add(host);
    }
    if (!hostsOk) missing.push("ADMIN_ALLOWED_HOSTS");
  }

  return {
    ok: missing.length === 0,
    missing,
    clientId,
    clientSecret,
    sessionSecret,
    emails: new Set(emails),
    hosts,
  };
}

export function storageBinding(env = {}) {
  return env.ADMIN_DB || null;
}
