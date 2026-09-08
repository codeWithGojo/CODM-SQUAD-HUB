#!/usr/bin/env node
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const url = process.env.DATABASE_URL?.trim();

if (!url) {
  console.log("migrate-vercel: DATABASE_URL is unset; skipping schema apply. Set it on Vercel before expecting saved workspaces.");
  process.exit(0);
}

if (!/^(postgres|postgresql):/i.test(url)) {
  console.error("migrate-vercel: DATABASE_URL must be a postgres connection string.");
  process.exit(1);
}

const pg = await import("pg").catch(() => null);
const Pool = pg?.Pool ?? pg?.default?.Pool;
if (!Pool) {
  console.error("migrate-vercel: install pg (`npm i pg`) before applying the Vercel schema.");
  process.exit(1);
}

const dir = path.join(root, "drizzle", "postgres");
const files = (await readdir(dir)).filter(name => name.endsWith(".sql")).sort();
const ssl = /sslmode=require/i.test(url) || process.env.VERCEL === "1" ? { rejectUnauthorized: false } : undefined;
const pool = new Pool({ connectionString: url, ssl });
try {
  for (const file of files) {
    const sql = await readFile(path.join(dir, file), "utf8");
    await pool.query(sql);
    console.log(`migrate-vercel: applied ${file}`);
  }
} finally {
  await pool.end();
}
