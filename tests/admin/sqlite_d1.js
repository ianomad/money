import { DatabaseSync } from "node:sqlite";

export function createSqliteD1() {
  const db = new DatabaseSync(":memory:");
  return {
    prepare(sql) {
      const statement = {
        params: [],
        bind(...params) {
          statement.params = params;
          return statement;
        },
        async run() {
          const info = db.prepare(sql).run(...statement.params);
          return { success: true, meta: { changes: Number(info.changes) } };
        },
        async first() {
          return db.prepare(sql).get(...statement.params) ?? null;
        },
        async all() {
          return { results: db.prepare(sql).all(...statement.params) };
        },
      };
      return statement;
    },
    async batch(statements) {
      db.exec("BEGIN");
      try {
        const results = [];
        for (const statement of statements) results.push(await statement.run());
        db.exec("COMMIT");
        return results;
      } catch (error) {
        db.exec("ROLLBACK");
        throw error;
      }
    },
  };
}
