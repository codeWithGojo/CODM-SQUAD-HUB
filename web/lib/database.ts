import { StoreError, type Database, type Statement } from "./store.ts";

export type SqlDialect = "sqlite" | "postgres";

export function rewriteSql(sql: string, dialect: SqlDialect): string {
  if (dialect === "sqlite") return sql;
  let rewritten = sql.replace(
    /\bjson_extract\(\s*body\s*,\s*'\$\.rules\.name'\s*\)/gi,
    "body::jsonb #>> '{rules,name}'",
  );
  let index = 0;
  rewritten = rewritten.replace(/\?/g, () => `$${++index}`);
  return rewritten;
}

function asRecord(row: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(row)) {
    out[key] = typeof value === "object" && value !== null && !(value instanceof Date)
      ? JSON.stringify(value)
      : value;
  }
  return out;
}

type QueryResult = { rows: Record<string, unknown>[]; changes: number };

function statements(run: (sql: string, params: unknown[]) => Promise<QueryResult>, dialect: SqlDialect): Database {
  return {
    prepare(sql: string): Statement {
      const text = rewriteSql(sql, dialect);
      const statement: Statement & { params: unknown[] } = {
        params: [],
        bind(...args: unknown[]) {
          this.params = args;
          return this;
        },
        async first<T>() {
          const { rows } = await run(text, this.params);
          return (rows[0] ? asRecord(rows[0]) : null) as T | null;
        },
        async all<T>() {
          const { rows } = await run(text, this.params);
          return { results: rows.map(row => asRecord(row)) as T[] };
        },
        async run() {
          const { changes } = await run(text, this.params);
          return { meta: { changes } };
        },
      };
      return statement;
    },
  };
}

type NodeSqlite = {
  prepare(sql: string): {
    get(...params: unknown[]): Record<string, unknown> | undefined;
    all(...params: unknown[]): Record<string, unknown>[];
    run(...params: unknown[]): { changes: number };
  };
};

export function wrapNodeSqlite(db: NodeSqlite): Database {
  return {
    prepare(sql: string): Statement {
      const statement: Statement & { params: unknown[] } = {
        params: [],
        bind(...args: unknown[]) {
          this.params = args;
          return this;
        },
        async first<T>() {
          return (db.prepare(sql).get(...this.params) ?? null) as T | null;
        },
        async all<T>() {
          return { results: db.prepare(sql).all(...this.params) as T[] };
        },
        async run() {
          return { meta: { changes: db.prepare(sql).run(...this.params).changes } };
        },
      };
      return statement;
    },
  };
}

type PgPool = {
  query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[]; rowCount: number | null }>;
};

const globalRef = globalThis as typeof globalThis & { __squadHubPg?: PgPool };

async function postgresPool(url: string): Promise<PgPool> {
  if (globalRef.__squadHubPg) return globalRef.__squadHubPg;
  const pg = await import("pg") as { Pool: new (config: object) => PgPool; default?: { Pool: new (config: object) => PgPool } };
  const Pool = pg.Pool ?? pg.default?.Pool;
  if (!Pool) throw new StoreError("The Postgres adapter requires the pg package.", 503);
  const ssl = /sslmode=require/i.test(url) || process.env.VERCEL === "1" ? { rejectUnauthorized: false } : undefined;
  globalRef.__squadHubPg = new Pool({ connectionString: url, max: 5, ssl });
  return globalRef.__squadHubPg;
}

async function tryCloudflareDb(): Promise<Database | null> {
  if (process.env.VERCEL === "1" || process.env.DATABASE_URL) return null;
  try {
    const mod = await import("cloudflare:workers");
    const db = (mod as { env?: { DB?: Database } }).env?.DB;
    return db ?? null;
  } catch {
    return null;
  }
}

async function sqliteFile(path: string): Promise<Database> {
  const { DatabaseSync } = await import("node:sqlite");
  return wrapNodeSqlite(new DatabaseSync(path));
}

export async function getDatabase(): Promise<Database> {
  const url = process.env.DATABASE_URL?.trim();
  if (url && /^(postgres|postgresql):/i.test(url)) {
    const pool = await postgresPool(url);
    return statements(async (sql, params) => {
      const result = await pool.query(sql, params);
      return { rows: result.rows, changes: result.rowCount ?? 0 };
    }, "postgres");
  }
  if (process.env.SQLITE_PATH) return sqliteFile(process.env.SQLITE_PATH);
  const cloudflare = await tryCloudflareDb();
  if (cloudflare) return cloudflare;
  throw new StoreError("Saved records are unavailable until this update is deployed with its database. Your form has not been submitted.", 503);
}
