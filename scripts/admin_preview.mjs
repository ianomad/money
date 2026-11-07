// Local UI preview only. Cloudflare never runs this file.
// Production entrypoint: functions/admin/[[path]].js, which cannot mint a session.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { handleAdminRequest } from "../functions/_lib/admin/handlers.js";
import { signSession } from "../functions/_lib/admin/google.js";
import { renderUnconfigured } from "../functions/_lib/admin/page.js";
import { createMemoryStore } from "../functions/_lib/admin/store_memory.js";

const port = Number(process.env.PORT || 4173);
const secret = "preview-session-secret-not-used-in-prod";
const email = "preview@example.com";
const env = {
  GOOGLE_CLIENT_ID: "preview-client-id.apps.googleusercontent.com",
  GOOGLE_CLIENT_SECRET: "preview-client-secret",
  ADMIN_SESSION_SECRET: secret,
  ADMIN_EMAILS: email,
  ADMIN_ALLOWED_HOSTS: "127.0.0.1",
};
const store = createMemoryStore();
const session = await signSession(secret, { email, sub: "preview-sub" }, Date.now());

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:" + port);
  if (url.pathname === "/favicon.svg") {
    res.writeHead(200, { "content-type": "image/svg+xml", "cache-control": "no-store" });
    res.end(readFileSync(new URL("../docs/favicon.svg", import.meta.url)));
    return;
  }
  const mode = url.searchParams.get("view");
  if (mode === "unconfigured") {
    res.writeHead(503, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" });
    res.end(renderUnconfigured(["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "ADMIN_SESSION_SECRET", "ADMIN_EMAILS"]));
    return;
  }
  url.searchParams.delete("view");
  const body = req.method === "GET" || req.method === "HEAD" ? undefined : await readBody(req);
  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (value == null) continue;
    headers.set(key, Array.isArray(value) ? value.join(", ") : value);
  }
  if (!mode && !headers.get("cookie")) headers.set("cookie", "mb_admin_session=" + session);
  const request = new Request(url, { method: req.method, headers, body });
  const response = await handleAdminRequest(request, mode === "unconfigured" ? {} : env, {
    store: mode === "unconfigured" ? null : store,
    allowInsecureLocalhost: true,
    fetch: async () => { throw new Error("preview has no Google network"); },
  });
  const out = new Headers(response.headers);
  res.writeHead(response.status, Object.fromEntries(out));
  res.end(Buffer.from(await response.arrayBuffer()));
});

server.listen(port, "127.0.0.1", () => {
  console.log("http://127.0.0.1:" + port + "/admin");
});
