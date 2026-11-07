import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { onRequest } from "../../functions/_middleware.js";

test("public host redirect and search console behavior stay in place", async () => {
  let called = false;
  const home = await onRequest({
    request: new Request("https://getmoneybeast.com/rates"),
    next() {
      called = true;
      return new Response("ok", { status: 200 });
    },
  });
  assert.equal(called, true);
  assert.equal(home.status, 200);

  const www = await onRequest({
    request: new Request("https://www.getmoneybeast.com/rates?x=1"),
    next() { throw new Error("redirect should not continue"); },
  });
  assert.equal(www.status, 301);
  assert.equal(www.headers.get("location"), "https://getmoneybeast.com/rates?x=1");

  const old = await onRequest({
    request: new Request("https://money.ilyusha.xyz/cards"),
    next() { throw new Error("redirect should not continue"); },
  });
  assert.equal(old.status, 301);
  assert.equal(old.headers.get("location"), "https://getmoneybeast.com/cards");

  const verify = await onRequest({
    request: new Request("https://money.ilyusha.xyz/google84212aea3ca8c810.html"),
    next() { throw new Error("verification should not redirect"); },
  });
  assert.equal(verify.status, 200);
  assert.match(await verify.text(), /google-site-verification: google84212aea3ca8c810.html/);
});

test("public pages do not advertise the admin registry", () => {
  const home = readFileSync(new URL("../../docs/index.html", import.meta.url), "utf8");
  const robots = readFileSync(new URL("../../docs/robots.txt", import.meta.url), "utf8");
  assert.equal(home.includes('href="/admin"'), false);
  assert.match(home, /Money Beast/);
  assert.match(robots, /Disallow: \/admin/);
  assert.match(robots, /Sitemap: https:\/\/getmoneybeast.com\/sitemap\.xml/);
});

test("the private admin mailbox is not in source", () => {
  const files = [
    "functions/_middleware.js",
    "functions/admin/[[path]].js",
    "functions/_lib/admin/handlers.js",
    "functions/_lib/admin/client.js",
    "functions/_lib/admin/page.js",
    "functions/_lib/admin/seed.js",
    "functions/_lib/admin/config.js",
    "admin/SETUP.md",
    "docs/robots.txt",
    "package.json",
  ];
  for (const file of files) {
    let text = "";
    try {
      text = readFileSync(new URL("../../" + file, import.meta.url), "utf8");
    } catch {
      continue;
    }
    assert.equal(text.includes("ilyusha.connect@gmail.com"), false, file);
  }
});
