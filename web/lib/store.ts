import { applyCommand, emptyWorkspace, type Workspace, type Command, DomainError } from "./workspace.ts";
export interface Statement {bind(...args:unknown[]):Statement;first<T>():Promise<T|null>;all<T>():Promise<{results:T[]}>;run():Promise<{meta:{changes?:number}}>}
export interface Database {prepare(sql:string):Statement}
export class StoreError extends Error {status:number;constructor(message:string,status:number){super(message);this.status=status;}}
export async function readWorkspace(db:Database,owner:string,game:string){
 const row=await db.prepare("SELECT body, version, updated_at FROM workspaces WHERE owner = ? AND game = ?").bind(owner,game).first<{body:string;version:number;updated_at:string}>();
 return row?{workspace:JSON.parse(row.body) as Workspace,version:row.version,updatedAt:row.updated_at}:{workspace:emptyWorkspace(game),version:0,updatedAt:null};
}
export async function saveCommand(db:Database,owner:string,game:string,version:number,command:Command){
 const current=await readWorkspace(db,owner,game);
 if(!Number.isInteger(version)||version!==current.version)throw new StoreError("This game was changed in another tab. Reload the latest records and try again.",409);
 const now=new Date().toISOString(),workspace=applyCommand(current.workspace,command,now),body=JSON.stringify(workspace);
 if(new TextEncoder().encode(body).length>2_000_000)throw new DomainError("This game workspace is full. Export its records before creating another workspace.");
 let result;
 if(version===0)result=await db.prepare("INSERT INTO workspaces (owner, game, body, version, updated_at) VALUES (?, ?, ?, 1, ?) ON CONFLICT(owner, game) DO NOTHING").bind(owner,game,body,now).run();
 else result=await db.prepare("UPDATE workspaces SET body = ?, version = version + 1, updated_at = ? WHERE owner = ? AND game = ? AND version = ?").bind(body,now,owner,game,version).run();
 if(result.meta.changes!==1)throw new StoreError("Another save finished first. Reload the latest records and try again.",409);
 return {workspace,version:version+1,updatedAt:now};
}
