export const SCHEMA_VERSION = 1;
export const COMPONENT_TYPES = ["agent", "workflow", "data_source", "model", "evaluation", "service"];
export const COMPONENT_STATUSES = ["proposed", "active", "paused", "retired", "unavailable"];
export const RULE_STATUSES = ["draft", "active", "retired"];
export const ID_RE = /^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/;
const KIND_RE = /^[a-z0-9](?:[a-z0-9_-]{0,40})$/;

export const JSON_SCHEMA = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "https://getmoneybeast.com/admin/schema",
  title: "Money Beast admin registry",
  type: "object",
  properties: {
    schemaVersion: { const: SCHEMA_VERSION },
    effect: { const: "registry_only" },
    runtimeControl: { const: "none" },
    component: { $ref: "#/$defs/component" },
    rule: { $ref: "#/$defs/rule" },
  },
  $defs: {
    component: {
      type: "object",
      additionalProperties: false,
      required: ["id", "type", "name", "owner", "purpose", "status", "version", "provenance", "dependencies"],
      properties: {
        id: { type: "string", pattern: ID_RE.source },
        type: { enum: COMPONENT_TYPES },
        kind: { type: "string" },
        name: { type: "string", minLength: 1, maxLength: 120 },
        owner: { type: "string", minLength: 1, maxLength: 120 },
        purpose: { type: "string", minLength: 1, maxLength: 2000 },
        status: { enum: COMPONENT_STATUSES },
        version: { type: "string", minLength: 1, maxLength: 64 },
        provenance: { type: "string", minLength: 1, maxLength: 2000 },
        dependencies: { type: "array", maxItems: 32, items: { type: "string", pattern: ID_RE.source } },
        expectedRevision: { type: "integer", minimum: 1 },
      },
    },
    rule: {
      type: "object",
      additionalProperties: false,
      required: ["id", "name", "scope", "statement", "status", "affected"],
      properties: {
        id: { type: "string", pattern: ID_RE.source },
        name: { type: "string", minLength: 1, maxLength: 160 },
        scope: { type: "string" },
        statement: { type: "string", minLength: 1, maxLength: 8000 },
        status: { enum: RULE_STATUSES },
        affected: { type: "array", maxItems: 64, items: { type: "string", pattern: ID_RE.source } },
        expectedRevision: { type: "integer", minimum: 1 },
      },
    },
  },
};

function issue(path, message) {
  return { path, message };
}

function cleanText(value, path, { min, max }, issues) {
  if (typeof value !== "string") {
    issues.push(issue(path, "Must be text."));
    return "";
  }
  const text = value.trim();
  if (text.length < min) issues.push(issue(path, min === 1 ? "Required." : "Too short."));
  if (text.length > max) issues.push(issue(path, "Too long."));
  return text;
}

function cleanIdList(value, path, max, issues) {
  if (!Array.isArray(value)) {
    issues.push(issue(path, "Must be a list of ids."));
    return [];
  }
  if (value.length > max) issues.push(issue(path, "Too many ids."));
  const out = [];
  for (const item of value) {
    if (typeof item !== "string" || !ID_RE.test(item)) {
      issues.push(issue(path, "Each id must be a lowercase slug."));
      return out;
    }
    if (!out.includes(item)) out.push(item);
  }
  return out;
}

export function parseScope(scope) {
  if (scope === "global") return { kind: "global" };
  if (typeof scope !== "string") return null;
  if (scope.startsWith("type:")) {
    const type = scope.slice(5);
    if (!COMPONENT_TYPES.includes(type)) return null;
    return { kind: "type", type };
  }
  if (scope.startsWith("component:")) {
    const id = scope.slice("component:".length);
    if (!ID_RE.test(id)) return null;
    return { kind: "component", id };
  }
  return null;
}

export function validateComponentInput(input, { requireRevision = false } = {}) {
  const issues = [];
  const source = input && typeof input === "object" ? input : {};
  const id = cleanText(source.id, "id", { min: 1, max: 64 }, issues);
  if (id && !ID_RE.test(id)) issues.push(issue("id", "Use a lowercase slug, 1–64 characters."));
  const type = source.type;
  if (!COMPONENT_TYPES.includes(type)) issues.push(issue("type", "Choose a supported component type."));
  let kind = "";
  if (source.kind != null && String(source.kind).trim() !== "") {
    kind = String(source.kind).trim();
    if (!KIND_RE.test(kind)) issues.push(issue("kind", "Use a short lowercase label such as fine_tuned."));
  }
  const name = cleanText(source.name, "name", { min: 1, max: 120 }, issues);
  const owner = cleanText(source.owner, "owner", { min: 1, max: 120 }, issues);
  const purpose = cleanText(source.purpose, "purpose", { min: 1, max: 2000 }, issues);
  const status = source.status;
  if (!COMPONENT_STATUSES.includes(status)) issues.push(issue("status", "Choose a lifecycle status."));
  const version = cleanText(source.version, "version", { min: 1, max: 64 }, issues);
  const provenance = cleanText(source.provenance, "provenance", { min: 1, max: 2000 }, issues);
  const dependencies = cleanIdList(source.dependencies, "dependencies", 32, issues);
  if (dependencies.includes(id)) issues.push(issue("dependencies", "A component cannot depend on itself."));
  let expectedRevision;
  if (requireRevision || source.expectedRevision != null) {
    expectedRevision = source.expectedRevision;
    if (!Number.isInteger(expectedRevision) || expectedRevision < 1) {
      issues.push(issue("expectedRevision", "A whole-number revision is required."));
    }
  }
  return {
    ok: issues.length === 0,
    issues,
    value: { id, type, kind, name, owner, purpose, status, version, provenance, dependencies, expectedRevision },
  };
}

export function validateRuleInput(input, { requireRevision = false } = {}) {
  const issues = [];
  const source = input && typeof input === "object" ? input : {};
  const id = cleanText(source.id, "id", { min: 1, max: 64 }, issues);
  if (id && !ID_RE.test(id)) issues.push(issue("id", "Use a lowercase slug, 1–64 characters."));
  const name = cleanText(source.name, "name", { min: 1, max: 160 }, issues);
  const scope = typeof source.scope === "string" ? source.scope.trim() : "";
  if (!parseScope(scope)) issues.push(issue("scope", "Use global, type:<type>, or component:<id>."));
  const statement = cleanText(source.statement, "statement", { min: 1, max: 8000 }, issues);
  const status = source.status;
  if (!RULE_STATUSES.includes(status)) issues.push(issue("status", "Choose draft, active, or retired."));
  const affected = cleanIdList(source.affected, "affected", 64, issues);
  let expectedRevision;
  if (requireRevision || source.expectedRevision != null) {
    expectedRevision = source.expectedRevision;
    if (!Number.isInteger(expectedRevision) || expectedRevision < 1) {
      issues.push(issue("expectedRevision", "A whole-number revision is required."));
    }
  }
  return {
    ok: issues.length === 0,
    issues,
    value: { id, name, scope, statement, status, affected, expectedRevision },
  };
}

export function presentComponent(row) {
  return {
    schemaVersion: SCHEMA_VERSION,
    id: row.id,
    type: row.type,
    kind: row.kind || "",
    name: row.name,
    owner: row.owner,
    purpose: row.purpose,
    status: row.status,
    version: row.version,
    provenance: row.provenance,
    dependencies: [...row.dependencies],
    revision: row.revision,
    updatedAt: row.updatedAt,
    updatedBy: row.updatedBy,
    effect: "registry_only",
    runtimeControl: "none",
  };
}

export function presentRule(row, resolvedAffected = []) {
  return {
    schemaVersion: SCHEMA_VERSION,
    id: row.id,
    name: row.name,
    scope: row.scope,
    statement: row.statement,
    status: row.status,
    affected: [...row.affected],
    resolvedAffected: [...resolvedAffected],
    version: row.version,
    revision: row.revision,
    updatedAt: row.updatedAt,
    updatedBy: row.updatedBy,
    effect: "registry_only",
    runtimeControl: "none",
  };
}

export function sameComponent(a, b) {
  return a.type === b.type && a.kind === b.kind && a.name === b.name && a.owner === b.owner
    && a.purpose === b.purpose && a.status === b.status && a.version === b.version
    && a.provenance === b.provenance && JSON.stringify(a.dependencies) === JSON.stringify(b.dependencies);
}

export function sameRule(a, b) {
  return a.name === b.name && a.scope === b.scope && a.statement === b.statement
    && a.status === b.status && JSON.stringify(a.affected) === JSON.stringify(b.affected);
}
