import assert from "node:assert/strict";
import test from "node:test";
import { buildMetrics } from "../../functions/_lib/admin/metrics.js";
import { adminFetch, createStore, signIn } from "./harness.js";

const NOW = "2026-11-07T12:00:00.000Z";

test("metrics stay honest about freshness, emptiness, and missing adapters", async () => {
  const store = createStore("memory");
  await store.seedIfEmpty(NOW);
  const counts = await store.counts();
  const body = buildMetrics({ now: NOW, storage: true, counts });
  assert.match(body.note, /No historical chart/);
  for (const source of body.sources) {
    assert.deepEqual(source.series, []);
    assert.equal(source.value, null);
    assert.equal(JSON.stringify(source).includes('"requests"'), false);
  }
  const registry = body.sources.find((source) => source.id === "registry");
  assert.equal(registry.status, "ok");
  assert.equal(registry.counts.byType.agent, 0);
  assert.equal(registry.counts.byType.model, 0);
  assert.equal(registry.counts.byType.evaluation, 0);
  assert.equal(registry.counts.components, 5);
  const rates = body.sources.find((source) => source.id === "dataset:rates");
  assert.equal(rates.status, "ok");
  assert.equal(rates.checkedAt, "2026-11-06");
  assert.equal(rates.provenance.includes("data/rates.json"), true);
  for (const id of ["runtime_health", "job_results", "evaluations", "usage"]) {
    assert.equal(body.sources.find((source) => source.id === id).status, "unavailable");
  }

  const stale = buildMetrics({
    now: NOW,
    storage: false,
    files: [
      { id: "old", label: "Old file", file: "data/old.json", timeField: "checkedAt", checkedAt: "2020-01-01" },
      { id: "bad", label: "Bad file", file: "data/bad.json", timeField: "checkedAt", checkedAt: "not-a-date" },
    ],
  });
  assert.equal(stale.sources.find((source) => source.id === "registry").status, "disconnected");
  assert.equal(stale.sources.find((source) => source.id === "dataset:old").status, "stale");
  assert.equal(stale.sources.find((source) => source.id === "dataset:bad").status, "unavailable");
  assert.equal(stale.sources.some((source) => source.kind === "dataset_freshness" && source.checkedAt === "2026-11-06"), false);

  const session = await signIn();
  const live = await adminFetch("https://getmoneybeast.com/admin/api/metrics", { session, store });
  assert.equal(live.status, 200);
  const json = JSON.stringify(await live.json());
  assert.equal(json.includes("G-7WGRRRQQRB"), false);
  assert.equal(/"users":\s*\d/.test(json), false);
});
