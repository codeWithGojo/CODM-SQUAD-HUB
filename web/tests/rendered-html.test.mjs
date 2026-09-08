import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
test('production build contains the saved-workspace migration',async()=>{
 const manifest=JSON.parse(await readFile(new URL('../dist/.openai/hosting.json',import.meta.url),'utf8'));
 assert.equal(manifest.project_id,'appgprj_6a79655c969c8191b6438f8a44cc61b0');
 assert.equal(manifest.d1,'DB');
 const sql=await readFile(new URL('../dist/.openai/drizzle/0000_public_skrulls.sql',import.meta.url),'utf8');
 assert.match(sql,/PRIMARY KEY\(`owner`, `game`\)/);
 const worker=await readFile(new URL('../dist/server/index.js',import.meta.url),'utf8');
 assert.ok(worker.length>0);
});
