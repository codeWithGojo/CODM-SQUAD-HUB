import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
const manifest=JSON.parse(await readFile('dist/.openai/hosting.json','utf8'));
assert.equal(manifest.d1,'DB');
// Offline integration test: substitute only the Workers environment binding.
// Authentication, routes and SQL run from the real production bundle.
const sqlite=new DatabaseSync(':memory:');
sqlite.exec(await readFile('drizzle/0000_public_skrulls.sql','utf8'));
const db={prepare(sql){return {params:[],bind(...args){this.params=args;return this;},async first(){return sqlite.prepare(sql).get(...this.params)??null;},async all(){return {results:sqlite.prepare(sql).all(...this.params)};},async run(){return {meta:{changes:sqlite.prepare(sql).run(...this.params).changes}};}};}};
globalThis.__squadHubTestEnv={DB:db};
const hook=registerHooks({resolve(specifier,context,nextResolve){if(specifier==='cloudflare:workers')return {url:'data:text/javascript,export const env=globalThis.__squadHubTestEnv;',shortCircuit:true};return nextResolve(specifier,context);}});
try{
 const {default:worker}=await import(pathToFileURL(process.cwd()+'/dist/server/index.js').href);
 assert.equal(typeof worker.fetch,'function');
 const dispatch=(url,init)=>worker.fetch(new Request(url,init),{DB:db,ASSETS:{fetch:async()=>new Response('Not found',{status:404})}},{waitUntil(){},passThroughOnException(){}});
 const endpoint='http://localhost/api/workspace';
 const anonymous=await dispatch(endpoint+'?game=codm');assert.equal(anonymous.status,401);
 const headers={'oai-authenticated-user-id':'validation-organizer','content-type':'application/json',origin:'http://localhost'};
 const denied=await dispatch(endpoint,{method:'POST',headers:{...headers,origin:'https://untrusted.example'},body:JSON.stringify({})});assert.equal(denied.status,403);
 const saved=await dispatch(endpoint,{method:'POST',headers,body:JSON.stringify({game:'codm',version:0,owner:'forged-owner',command:{type:'team.add',name:'Validation squad',tier:'First team'}})});
 assert.equal(saved.status,200,await saved.clone().text());const body=await saved.json();assert.equal(body.workspace.teams.length,1);
 const reloaded=await dispatch(endpoint+'?game=codm',{headers});assert.equal((await reloaded.json()).workspace.teams[0].name,'Validation squad');
 const otherGame=await dispatch(endpoint+'?game=valorant',{headers});assert.equal((await otherGame.json()).workspace.teams.length,0);
 const otherUser=await dispatch(endpoint+'?game=codm',{headers:{'oai-authenticated-user-id':'forged-owner'}});assert.equal((await otherUser.json()).workspace.teams.length,0);
 const conflict=await dispatch(endpoint,{method:'POST',headers,body:JSON.stringify({game:'codm',version:0,command:{type:'team.add',name:'Duplicate',tier:'First team'}})});assert.equal(conflict.status,409);
 const page=await dispatch('http://localhost/',{headers:{accept:'text/html'}});assert.equal(page.status,200);const html=await page.text();assert.match(html,/Your competitive workspace/);assert.match(html,/SquadHub/);assert.doesNotMatch(html,/African CODM, properly organized/);
 console.log('Validated production-bundle fetch, server rendering, authentication, origin checks, SQLite persistence, isolation and conflicts (offline binding adapter).');
}finally{hook.deregister();sqlite.close();delete globalThis.__squadHubTestEnv;}
