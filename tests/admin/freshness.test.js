import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { manifest } from "../../functions/_lib/admin/freshness_data.js";

test("bundled dataset timestamps match the repository files", () => {
  assert.equal(manifest.files.length > 0, true);
  for (const file of manifest.files) {
    const json = JSON.parse(readFileSync(new URL("../../" + file.file, import.meta.url), "utf8"));
    assert.equal(json[file.timeField], file.checkedAt, file.file);
  }
});
