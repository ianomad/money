import { buildSeed } from "./seed.js";
import { sameComponent, sameRule } from "./schema.js";

function clone(value) {
  return structuredClone(value);
}

export function createMemoryStore() {
  const components = new Map();
  const rules = new Map();
  const versions = [];
  const audit = [];
  let seeded = false;
  let auditId = 0;

  function addAudit(entry) {
    auditId += 1;
    audit.push({ id: auditId, ...entry });
  }

  function dependentsOf(id) {
    return [...components.values()]
      .filter((row) => row.id !== id && row.dependencies.includes(id))
      .map((row) => ({ id: row.id, name: row.name, type: row.type }));
  }

  function rulesUsing(id) {
    return [...rules.values()]
      .filter((row) => row.scope === "component:" + id || row.affected.includes(id))
      .map((row) => ({ id: row.id, name: row.name }));
  }

  return {
    kind: "memory",
    async seedIfEmpty(now) {
      if (seeded) return false;
      const seed = buildSeed(now);
      for (const component of seed.components) components.set(component.id, clone(component));
      for (const rule of seed.rules) {
        rules.set(rule.id, clone(rule));
        versions.push({
          ruleId: rule.id,
          version: rule.version,
          snapshot: clone(rule),
          createdAt: now,
          createdBy: "system",
        });
      }
      addAudit({
        at: now,
        actor: "system",
        action: "seed",
        entityType: "registry",
        entityId: "registry",
        fromRevision: null,
        toRevision: 1,
        summary: "Seeded " + seed.components.length + " components and " + seed.rules.length + " rule from this repository.",
      });
      seeded = true;
      return true;
    },
    async counts() {
      const byType = {};
      const byStatus = {};
      for (const row of components.values()) {
        byType[row.type] = (byType[row.type] || 0) + 1;
        byStatus[row.status] = (byStatus[row.status] || 0) + 1;
      }
      return {
        components: components.size,
        rules: rules.size,
        byType,
        byStatus,
        lastAuditAt: audit.length ? audit[audit.length - 1].at : null,
      };
    },
    async listComponents() {
      return [...components.values()].map(clone);
    },
    async getComponent(id) {
      return components.has(id) ? clone(components.get(id)) : null;
    },
    async dependents(id) {
      return dependentsOf(id);
    },
    async insertComponent(row, actor, now) {
      if (components.has(row.id)) return { exists: true };
      if (components.size >= 200) return { limit: true };
      const record = { ...row, revision: 1, updatedAt: now, updatedBy: actor };
      components.set(record.id, record);
      addAudit({
        at: now, actor, action: "create", entityType: "component", entityId: record.id,
        fromRevision: null, toRevision: 1, summary: "Created component " + record.name + ".",
      });
      return { record: clone(record) };
    },
    async updateComponent(id, next, expectedRevision, actor, now) {
      const current = components.get(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current: clone(current) };
      if (sameComponent(current, next)) return { record: clone(current) };
      const record = { ...current, ...next, id, revision: current.revision + 1, updatedAt: now, updatedBy: actor };
      components.set(id, record);
      addAudit({
        at: now, actor, action: "update", entityType: "component", entityId: id,
        fromRevision: current.revision, toRevision: record.revision, summary: "Updated component " + record.name + ".",
      });
      return { record: clone(record) };
    },
    async deleteComponent(id, expectedRevision, actor, now) {
      const current = components.get(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current: clone(current) };
      const dependents = dependentsOf(id);
      const rules = rulesUsing(id);
      if (dependents.length || rules.length) return { inUse: true, dependents, rules };
      components.delete(id);
      addAudit({
        at: now, actor, action: "delete", entityType: "component", entityId: id,
        fromRevision: current.revision, toRevision: null, summary: "Deleted component " + current.name + ".",
      });
      return { deleted: true };
    },
    async listRules() {
      return [...rules.values()].map(clone);
    },
    async getRule(id) {
      return rules.has(id) ? clone(rules.get(id)) : null;
    },
    async ruleVersions(id) {
      return versions.filter((row) => row.ruleId === id).map(clone);
    },
    async insertRule(row, actor, now) {
      if (rules.has(row.id)) return { exists: true };
      if (rules.size >= 200) return { limit: true };
      const record = { ...row, version: 1, revision: 1, updatedAt: now, updatedBy: actor };
      rules.set(record.id, record);
      versions.push({ ruleId: record.id, version: 1, snapshot: clone(record), createdAt: now, createdBy: actor });
      addAudit({
        at: now, actor, action: "create", entityType: "rule", entityId: record.id,
        fromRevision: null, toRevision: 1, summary: "Created rule " + record.name + " version 1.",
      });
      return { record: clone(record) };
    },
    async updateRule(id, next, expectedRevision, actor, now) {
      const current = rules.get(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current: clone(current) };
      if (sameRule(current, next)) return { record: clone(current) };
      const record = {
        ...current,
        ...next,
        id,
        version: current.version + 1,
        revision: current.revision + 1,
        updatedAt: now,
        updatedBy: actor,
      };
      rules.set(id, record);
      versions.push({
        ruleId: id, version: record.version, snapshot: clone(record), createdAt: now, createdBy: actor,
      });
      addAudit({
        at: now, actor, action: "update", entityType: "rule", entityId: id,
        fromRevision: current.revision, toRevision: record.revision,
        summary: "Updated rule " + record.name + " to version " + record.version + ".",
      });
      return { record: clone(record) };
    },
    async deleteRule(id, expectedRevision, actor, now) {
      const current = rules.get(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current: clone(current) };
      rules.delete(id);
      addAudit({
        at: now, actor, action: "delete", entityType: "rule", entityId: id,
        fromRevision: current.revision, toRevision: null, summary: "Deleted rule " + current.name + ".",
      });
      return { deleted: true };
    },
    async listAudit(limit) {
      return audit.slice(-limit).reverse().map(clone);
    },
  };
}
