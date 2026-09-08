import { env } from "cloudflare:workers";
import { defaultGame } from "../../../lib/games";
import { DomainError } from "../../../lib/workspace";
import { readWorkspace, saveCommand, StoreError, type Database } from "../../../lib/store";
export const dynamic="force-dynamic";
const json=(body:unknown,status=200)=>Response.json(body,{status,headers:{"Cache-Control":"private, no-store","Vary":"Cookie","X-Content-Type-Options":"nosniff"}});
function context(req:Request){
 const owner=req.headers.get("oai-authenticated-user-id");
 if(!owner)throw new StoreError("Sign in to load your saved workspace.",401);
 const db=(env as unknown as {DB?:Database}).DB;
 if(!db)throw new StoreError("Saved records are unavailable until this update is deployed with its database. Your form has not been submitted.",503);
 return {owner,db};
}
function error(e:unknown){
 if(e instanceof StoreError)return json({error:e.message},e.status);
 if(e instanceof DomainError)return json({error:e.message},400);
 console.error("Workspace operation failed",e instanceof Error?e.message:"unknown error");
 return json({error:"Could not access saved records. Please try again; your input has been kept."},503);
}
export async function GET(req:Request){try{
 const {owner,db}=context(req);const game=new URL(req.url).searchParams.get("game");
 if(!game){
  const {results}=await db.prepare("SELECT game, json_extract(body, '$.rules.name') AS name, updated_at FROM workspaces WHERE owner = ? ORDER BY updated_at DESC LIMIT 100").bind(owner).all<{game:string;name:string;updated_at:string}>();
  return json({games:results});
 }
 try{defaultGame(game);}catch{return json({error:"Unknown game."},400);}
 return json(await readWorkspace(db,owner,game));
}catch(e){return error(e);}}
export async function POST(req:Request){try{
 const {owner,db}=context(req);
 if(req.headers.get("sec-fetch-site")==="cross-site")return json({error:"Cross-site changes are not allowed."},403);
 const origin=req.headers.get("origin");if(origin&&origin!==new URL(req.url).origin)return json({error:"Request origin did not match this site."},403);
 if(!req.headers.get("content-type")?.includes("application/json"))return json({error:"Expected a JSON request."},415);
 const reader=req.body?.getReader();if(!reader)return json({error:"Missing request body."},400);
 const chunks:Uint8Array[]=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>32_768){await reader.cancel();return json({error:"This submission is too large."},413);}chunks.push(value);}
 let data;try{const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}data=JSON.parse(new TextDecoder().decode(bytes));}catch{return json({error:"Invalid JSON."},400);}
 if(!data||typeof data.game!=="string"||!data.command||typeof data.command!=="object")return json({error:"Invalid workspace action."},400);
 try{defaultGame(data.game);}catch{return json({error:"Unknown game."},400);}
 return json(await saveCommand(db,owner,data.game,data.version,data.command));
}catch(e){return error(e);}}
