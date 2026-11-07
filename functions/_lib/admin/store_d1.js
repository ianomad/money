import { buildSeed } from "./seed.js";
import { sameComponent, sameRule } from "./schema.js";

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS components (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL,
    version TEXT NOT NULL,
    provenance TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT '',
    dependencies TEXT NOT NULL,
    revision INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    scope TEXT NOT NULL,
    statement TEXT NOT NULL,
    status TEXT NOT NULL,
    affected TEXT NOT NULL,
    version INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS rule_versions (
    rule_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    snapshot TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    PRIMARY KEY (rule_id, version)
  )`,
  `CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    from_revision INTEGER,
    to_revision INTEGER,
    summary TEXT NOT NULL
  )`,
  `CREATE INDEX IF NOT EXISTS audit_at ON audit (at)`,
];

function parseList(value) {
  const parsed = JSON.parse(value || "[]");
  return Array.isArray(parsed) ? parsed : [];
}

function componentFromRow(row) {
  if (!row) return null;
  return {
    id: row.id,
    type: row.type,
    kind: row.kind || "",
    name: row.name,
    owner: row.owner,
    purpose: row.purpose,
    status: row.status,
    version: row.version,
    provenance: row.provenance,
    dependencies: parseList(row.dependencies),
    revision: Number(row.revision),
    updatedAt: row.updated_at,
    updatedBy: row.updated_by,
  };
}

function ruleFromRow(row) {
  if (!row) return null;
  return {
    id: row.id,
    name: row.name,
    scope: row.scope,
    statement: row.statement,
    status: row.status,
    affected: parseList(row.affected),
    version: Number(row.version),
    revision: Number(row.revision),
    updatedAt: row.updated_at,
    updatedBy: row.updated_by,
  };
}

export function createD1Store(db) {
  let ready;

  function ensure() {
    if (!ready) {
      ready = (async () => {
        for (const sql of SCHEMA) await db.prepare(sql).bind().run();
      })();
    }
    return ready;
  }

  async function audit(entry) {
    await db.prepare(
      `INSERT INTO audit (at, actor, action, entity_type, entity_id, from_revision, to_revision, summary)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    ).bind(
      entry.at, entry.actor, entry.action, entry.entityType, entry.entityId,
      entry.fromRevision, entry.toRevision, entry.summary,
    ).run();
  }

  function componentInsert(row) {
    return db.prepare(
      `INSERT INTO components
        (id, type, name, owner, purpose, status, version, provenance, kind, dependencies, revision, updated_at, updated_by)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    ).bind(
      row.id, row.type, row.name, row.owner, row.purpose, row.status, row.version, row.provenance,
      row.kind || "", JSON.stringify(row.dependencies), row.revision, row.updatedAt, row.updatedBy,
    );
  }

  return {
    kind: "d1",
    async seedIfEmpty(now) {
      await ensure();
      const existing = await db.prepare("SELECT value FROM schema_meta WHERE key = 'seeded'").bind().first();
      if (existing) return false;
      const seed = buildSeed(now);
      const statements = [
        db.prepare("INSERT INTO schema_meta (key, value) VALUES ('seeded', ?)").bind(now),
      ];
      for (const component of seed.components) statements.push(componentInsert(component));
      for (const rule of seed.rules) {
        statements.push(db.prepare(
          `INSERT INTO rules (id, name, scope, statement, status, affected, version, revision, updated_at, updated_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        ).bind(
          rule.id, rule.name, rule.scope, rule.statement, rule.status, JSON.stringify(rule.affected),
          rule.version, rule.revision, rule.updatedAt, rule.updatedBy,
        ));
        statements.push(db.prepare(
          `INSERT INTO rule_versions (rule_id, version, snapshot, created_at, created_by) VALUES (?, ?, ?, ?, ?)`,
        ).bind(rule.id, rule.version, JSON.stringify(rule), now, "system"));
      }
      statements.push(db.prepare(
        `INSERT INTO audit (at, actor, action, entity_type, entity_id, from_revision, to_revision, summary)
         VALUES (?, 'system', 'seed', 'registry', 'registry', NULL, 1, ?)`,
      ).bind(now, "Seeded " + seed.components.length + " components and " + seed.rules.length + " rule from this repository."));
      try {
        await db.batch(statements);
        return true;
      } catch (error) {
        const again = await db.prepare("SELECT value FROM schema_meta WHERE key = 'seeded'").bind().first();
        if (again) return false;
        throw error;
      }
    },
    async counts() {
      await ensure();
      const components = await db.prepare("SELECT type, status FROM components").bind().all();
      const rules = await db.prepare("SELECT COUNT(*) AS n FROM rules").bind().first();
      const last = await db.prepare("SELECT at FROM audit ORDER BY id DESC LIMIT 1").bind().first();
      const byType = {};
      const byStatus = {};
      for (const row of components.results || []) {
        byType[row.type] = (byType[row.type] || 0) + 1;
        byStatus[row.status] = (byStatus[row.status] || 0) + 1;
      }
      return {
        components: (components.results || []).length,
        rules: Number(rules?.n || 0),
        byType,
        byStatus,
        lastAuditAt: last?.at || null,
      };
    },
    async listComponents() {
      await ensure();
      const rows = await db.prepare("SELECT * FROM components ORDER BY name").bind().all();
      return (rows.results || []).map(componentFromRow);
    },
    async getComponent(id) {
      await ensure();
      return componentFromRow(await db.prepare("SELECT * FROM components WHERE id = ?").bind(id).first());
    },
    async dependents(id) {
      await ensure();
      const rows = await db.prepare("SELECT id, name, type, dependencies FROM components WHERE id != ?").bind(id).all();
      return (rows.results || [])
        .filter((row) => parseList(row.dependencies).includes(id))
        .map((row) => ({ id: row.id, name: row.name, type: row.type }));
    },
    async insertComponent(row, actor, now) {
      await ensure();
      const count = await db.prepare("SELECT COUNT(*) AS n FROM components").bind().first();
      if (Number(count?.n || 0) >= 200) return { limit: true };
      const record = { ...row, revision: 1, updatedAt: now, updatedBy: actor };
      try {
        await componentInsert(record).run();
      } catch {
        return { exists: true };
      }
      await audit({
        at: now, actor, action: "create", entityType: "component", entityId: record.id,
        fromRevision: null, toRevision: 1, summary: "Created component " + record.name + ".",
      });
      return { record };
    },
    async updateComponent(id, next, expectedRevision, actor, now) {
      await ensure();
      const current = await this.getComponent(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current };
      if (sameComponent(current, next)) return { record: current };
      const record = { ...current, ...next, id, revision: current.revision + 1, updatedAt: now, updatedBy: actor };
      const result = await db.prepare(
        `UPDATE components
         SET type = ?, name = ?, owner = ?, purpose = ?, status = ?, version = ?, provenance = ?, kind = ?,
             dependencies = ?, revision = ?, updated_at = ?, updated_by = ?
         WHERE id = ? AND revision = ?`,
      ).bind(
        record.type, record.name, record.owner, record.purpose, record.status, record.version, record.provenance,
        record.kind || "", JSON.stringify(record.dependencies), record.revision, record.updatedAt, record.updatedBy,
        id, expectedRevision,
      ).run();
      if (!result.meta || result.meta.changes !== 1) {
        const latest = await this.getComponent(id);
        return latest ? { conflict: true, current: latest } : { notFound: true };
      }
      await audit({
        at: now, actor, action: "update", entityType: "component", entityId: id,
        fromRevision: current.revision, toRevision: record.revision, summary: "Updated component " + record.name + ".",
      });
      return { record };
    },
    async deleteComponent(id, expectedRevision, actor, now) {
      await ensure();
      const current = await this.getComponent(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current };
      const dependents = await this.dependents(id);
      const rules = (await this.listRules())
        .filter((row) => row.scope === "component:" + id || row.affected.includes(id))
        .map((row) => ({ id: row.id, name: row.name }));
      if (dependents.length || rules.length) return { inUse: true, dependents, rules };
      const result = await db.prepare("DELETE FROM components WHERE id = ? AND revision = ?").bind(id, expectedRevision).run();
      if (!result.meta || result.meta.changes !== 1) return { conflict: true, current: await this.getComponent(id) };
      await audit({
        at: now, actor, action: "delete", entityType: "component", entityId: id,
        fromRevision: current.revision, toRevision: null, summary: "Deleted component " + current.name + ".",
      });
      return { deleted: true };
    },
    async listRules() {
      await ensure();
      const rows = await db.prepare("SELECT * FROM rules ORDER BY name").bind().all();
      return (rows.results || []).map(ruleFromRow);
    },
    async getRule(id) {
      await ensure();
      return ruleFromRow(await db.prepare("SELECT * FROM rules WHERE id = ?").bind(id).first());
    },
    async ruleVersions(id) {
      await ensure();
      const rows = await db.prepare(
        "SELECT version, snapshot, created_at, created_by FROM rule_versions WHERE rule_id = ? ORDER BY version",
      ).bind(id).all();
      return (rows.results || []).map((row) => ({
        ruleId: id,
        version: Number(row.version),
        snapshot: JSON.parse(row.snapshot),
        createdAt: row.created_at,
        createdBy: row.created_by,
      }));
    },
    async insertRule(row, actor, now) {
      await ensure();
      const count = await db.prepare("SELECT COUNT(*) AS n FROM rules").bind().first();
      if (Number(count?.n || 0) >= 200) return { limit: true };
      const record = { ...row, version: 1, revision: 1, updatedAt: now, updatedBy: actor };
      try {
        await db.batch([
          db.prepare(
            `INSERT INTO rules (id, name, scope, statement, status, affected, version, revision, updated_at, updated_by)
             VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?)`,
          ).bind(record.id, record.name, record.scope, record.statement, record.status, JSON.stringify(record.affected), now, actor),
          db.prepare(
            `INSERT INTO rule_versions (rule_id, version, snapshot, created_at, created_by) VALUES (?, 1, ?, ?, ?)`,
          ).bind(record.id, JSON.stringify(record), now, actor),
        ]);
      } catch {
        return { exists: true };
      }
      await audit({
        at: now, actor, action: "create", entityType: "rule", entityId: record.id,
        fromRevision: null, toRevision: 1, summary: "Created rule " + record.name + " version 1.",
      });
      return { record };
    },
    async updateRule(id, next, expectedRevision, actor, now) {
      await ensure();
      const current = await this.getRule(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current };
      if (sameRule(current, next)) return { record: current };
      const record = {
        ...current, ...next, id,
        version: current.version + 1,
        revision: current.revision + 1,
        updatedAt: now,
        updatedBy: actor,
      };
      const result = await db.prepare(
        `UPDATE rules
         SET name = ?, scope = ?, statement = ?, status = ?, affected = ?, version = ?, revision = ?, updated_at = ?, updated_by = ?
         WHERE id = ? AND revision = ?`,
      ).bind(
        record.name, record.scope, record.statement, record.status, JSON.stringify(record.affected),
        record.version, record.revision, record.updatedAt, record.updatedBy, id, expectedRevision,
      ).run();
      if (!result.meta || result.meta.changes !== 1) {
        const latest = await this.getRule(id);
        return latest ? { conflict: true, current: latest } : { notFound: true };
      }
      await db.prepare(
        `INSERT INTO rule_versions (rule_id, version, snapshot, created_at, created_by) VALUES (?, ?, ?, ?, ?)`,
      ).bind(id, record.version, JSON.stringify(record), now, actor).run();
      await audit({
        at: now, actor, action: "update", entityType: "rule", entityId: id,
        fromRevision: current.revision, toRevision: record.revision,
        summary: "Updated rule " + record.name + " to version " + record.version + ".",
      });
      return { record };
    },
    async deleteRule(id, expectedRevision, actor, now) {
      await ensure();
      const current = await this.getRule(id);
      if (!current) return { notFound: true };
      if (current.revision !== expectedRevision) return { conflict: true, current };
      const result = await db.prepare("DELETE FROM rules WHERE id = ? AND revision = ?").bind(id, expectedRevision).run();
      if (!result.meta || result.meta.changes !== 1) return { conflict: true, current: await this.getRule(id) };
      await audit({
        at: now, actor, action: "delete", entityType: "rule", entityId: id,
        fromRevision: current.revision, toRevision: null, summary: "Deleted rule " + current.name + ".",
      });
      return { deleted: true };
    },
    async listAudit(limit) {
      await ensure();
      const rows = await db.prepare(
        "SELECT id, at, actor, action, entity_type, entity_id, from_revision, to_revision, summary FROM audit ORDER BY id DESC LIMIT ?",
      ).bind(limit).all();
      return (rows.results || []).map((row) => ({
        id: Number(row.id),
        at: row.at,
        actor: row.actor,
        action: row.action,
        entityType: row.entity_type,
        entityId: row.entity_id,
        fromRevision: row.from_revision == null ? null : Number(row.from_revision),
        toRevision: row.to_revision == null ? null : Number(row.to_revision),
        summary: row.summary,
      }));
    },
  };
}
