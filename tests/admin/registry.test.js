import assert from "node:assert/strict";
import test from "node:test";
import { ADMIN, adminFetch, createStore, signIn } from "./harness.js";

const origin = "https://getmoneybeast.com";

async function authed(kind) {
  const store = createStore(kind);
  const session = await signIn();
  const call = (path, options = {}) => adminFetch(origin + path, { store, session, ...options });
  return { store, call };
}

for (const kind of ["memory", "d1"]) {
  test("seed, validation, concurrency, and audit on " + kind, async () => {
    const { call } = await authed(kind);
    const listed = await call("/admin/api/components");
    assert.equal(listed.status, 200);
    const body = await listed.json();
    assert.equal(body.effect, "registry_only");
    const ids = body.components.map((item) => item.id).sort();
    assert.deepEqual(ids, ["editorial-datasets", "host-redirect", "pages-deploy", "public-site", "site-builders"]);
    assert.equal(body.components.every((item) => item.runtimeControl === "none"), true);
    assert.equal(body.components.some((item) => item.type === "agent" || item.type === "model" || item.type === "evaluation"), false);

    const bad = await call("/admin/api/components", {
      method: "POST",
      body: {
        id: "Bad Id",
        type: "bot",
        name: "Nope",
        owner: "Money Beast",
        purpose: "nope",
        status: "running",
        version: "1",
        provenance: "test",
        dependencies: ["public-site'; drop table components;--"],
        updatedBy: "attacker@example.com",
        runtimeControl: "pause",
      },
    });
    assert.equal(bad.status, 400);
    const issues = (await bad.json()).issues.map((issue) => issue.path);
    assert.equal(issues.includes("id"), true);
    assert.equal(issues.includes("type"), true);

    const created = await call("/admin/api/components", {
      method: "POST",
      body: {
        id: "rate-eval",
        type: "evaluation",
        kind: "hand_graded",
        name: "Public prediction grades",
        owner: "Money Beast",
        purpose: "A registry placeholder for grades that already live in the public prediction record.",
        status: "proposed",
        version: "0",
        provenance: "Created in the admin registry during a test. Not a connected evaluator.",
        dependencies: ["editorial-datasets"],
        updatedBy: "attacker@example.com",
      },
    });
    assert.equal(created.status, 201);
    const component = (await created.json()).component;
    assert.equal(component.revision, 1);
    assert.equal(component.updatedBy, ADMIN);
    assert.equal(component.runtimeControl, "none");

    const conflict = await call("/admin/api/components/rate-eval", {
      method: "PATCH",
      body: { ...component, purpose: "Updated purpose for the registry only.", expectedRevision: 1, revision: 99 },
    });
    assert.equal(conflict.status, 200);
    const updated = (await conflict.json()).component;
    assert.equal(updated.revision, 2);
    const stale = await call("/admin/api/components/rate-eval", {
      method: "PATCH",
      body: { ...component, purpose: "Stale write", expectedRevision: 1 },
    });
    assert.equal(stale.status, 409);
    assert.equal((await stale.json()).error, "revision_conflict");
    const still = await call("/admin/api/components/rate-eval");
    assert.match((await still.json()).component.purpose, /Updated purpose/);

    const blocked = await call("/admin/api/components/editorial-datasets", {
      method: "DELETE",
      body: { expectedRevision: 1 },
    });
    assert.equal(blocked.status, 409);
    assert.equal((await blocked.json()).error, "in_use");

    const rule = await call("/admin/api/rules", {
      method: "POST",
      body: {
        id: "label-only",
        name: "Paused is a label",
        scope: "component:rate-eval",
        statement: "Setting a component to paused changes this registry record only.",
        status: "active",
        affected: ["public-site"],
      },
    });
    assert.equal(rule.status, 201);
    const savedRule = (await rule.json()).rule;
    assert.equal(savedRule.version, 1);
    assert.equal(savedRule.resolvedAffected.includes("rate-eval"), true);
    assert.equal(savedRule.resolvedAffected.includes("public-site"), true);
    const revised = await call("/admin/api/rules/label-only", {
      method: "PATCH",
      body: { ...savedRule, statement: savedRule.statement + " It does not stop a workflow.", expectedRevision: savedRule.revision },
    });
    assert.equal(revised.status, 200);
    const versioned = await revised.json();
    assert.equal(versioned.rule.version, 2);
    const detail = await call("/admin/api/rules/label-only");
    const history = await detail.json();
    assert.equal(history.versions.length, 2);
    assert.equal(history.versions[0].snapshot.version, 1);
    const clash = await call("/admin/api/rules/label-only", {
      method: "PATCH",
      body: { ...savedRule, statement: "old", expectedRevision: 1 },
    });
    assert.equal(clash.status, 409);

    const audit = await call("/admin/api/audit?limit=20");
    const entries = (await audit.json()).entries;
    assert.equal(entries.some((entry) => entry.action === "seed" && entry.actor === "system"), true);
    assert.equal(entries.some((entry) => entry.entityId === "rate-eval" && entry.actor === ADMIN && entry.action === "update"), true);
    assert.equal(JSON.stringify(entries).includes("attacker@example.com"), false);

    const removed = await call("/admin/api/components/rate-eval", {
      method: "DELETE",
      body: { expectedRevision: updated.revision },
    });
    assert.equal(removed.status, 409);
    await call("/admin/api/rules/label-only", { method: "DELETE", body: { expectedRevision: 2 } });
    const removedAfter = await call("/admin/api/components/rate-eval", {
      method: "DELETE",
      body: { expectedRevision: updated.revision },
    });
    assert.equal(removedAfter.status, 200);
    const after = await call("/admin/api/audit?limit=5");
    assert.equal((await after.json()).entries.some((entry) => entry.action === "delete" && entry.entityId === "rate-eval"), true);
  });
}

test("storage disconnect is explicit", async () => {
  const session = await signIn();
  const components = await adminFetch(origin + "/admin/api/components", { session });
  assert.equal(components.status, 503);
  assert.equal((await components.json()).error, "storage_unconfigured");
  const metrics = await adminFetch(origin + "/admin/api/metrics", { session });
  const body = await metrics.json();
  const registry = body.sources.find((source) => source.id === "registry");
  assert.equal(registry.status, "disconnected");
  assert.equal(registry.value, null);
  assert.deepEqual(registry.series, []);
});
