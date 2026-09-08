import { defaultGame, type GameRules } from "./games.ts";
export type Player = {id:string;tag:string;uid:string;role:string;country:string;age:"adult"|"minor"|"unknown"};
export type Team = {id:string;name:string;tier:string;players:string[]};
export type Event = {id:string;name:string;mode:string;season:string;region:string;format:"league"|"knockout"|"placement";official:boolean;teamSize:number;bestOf:number;winPoints:number;placementPoints:number[];killPoints:number;teams:string[];status:"registration"|"running"|"complete"};
export type Match = {id:string;eventId:string;round:number;slot:number;teams:string[];scores:number[];kills:number[];status:"scheduled"|"submitted"|"approved"|"disputed";evidence:string;note:string;winner:string|null;updatedAt:string};
export type Transfer = {id:string;playerId:string;from:string;to:string;kind:"Permanent"|"Loan";note:string;status:"proposed"|"completed"|"rejected";consent:boolean};
export type Task = {id:string;title:string;mode:string;notes:string;done:boolean;createdAt:string};
export type Guide = {id:string;title:string;mode:string;notes:string;url:string;updatedAt:string};
export type RoomNote = {id:string;teamId:string;text:string;at:string};
export type Workspace = {schemaVersion:1;rules:GameRules;players:Player[];teams:Team[];events:Event[];matches:Match[];transfers:Transfer[];tasks:Task[];guides:Guide[];room:RoomNote[];audit:{id:string;at:string;action:string}[]};
export type Command = {type:string;[key:string]:unknown};
export class DomainError extends Error { status=400; }
function fail(message:string):never {throw new DomainError(message);}
export function emptyWorkspace(game:string):Workspace { return {schemaVersion:1,rules:defaultGame(game),players:[],teams:[],events:[],matches:[],transfers:[],tasks:[],guides:[],room:[],audit:[]}; }
function str(v:unknown,label:string,max=100,optional=false):string { if(typeof v!=="string" || (!optional&&!v.trim()) || v.length>max) return fail(`${label} must be ${optional?"0":"1"}–${max} characters.`); return v.trim(); }
function num(v:unknown,min:number,max:number,label:string):number { if(typeof v!=="number" || !Number.isInteger(v) || v<min||v>max) return fail(`${label} must be a whole number from ${min} to ${max}.`); return v; }
function one<T extends string>(v:unknown,values:readonly T[],label:string):T { if(!values.includes(v as T)) return fail(`Choose a valid ${label}.`); return v as T; }
function texts(v:unknown,label:string):string[] { if(!Array.isArray(v)||v.length<1||v.length>20) return fail(`${label} needs 1–20 values.`); const a=v.map(x=>str(x,label,50)); if(new Set(a.map(x=>x.toLowerCase())).size!==a.length) return fail(`${label} contains duplicates.`); return a; }
function link(v:unknown):string {const s=str(v??"","Source link",1000,true);if(!s)return s;try{const u=new URL(s);if(u.protocol!=="https:"&&u.protocol!=="http:")return fail("Use an http or https source link.");return u.href;}catch(e){if(e instanceof DomainError)throw e;return fail("Enter a complete source URL.");}}
function found<T extends {id:string}>(list:T[],id:unknown,label:string):T{return list.find(x=>x.id===id)??fail(`${label} was not found in this game's workspace.`);}
function unique(list:string[],value:string,label:string){if(list.some(x=>x.toLowerCase()===value.toLowerCase()))fail(`${label} already exists for this game.`);}
function editableRoster(w:Workspace,teamId:string){if(w.events.some(e=>e.status!=="complete"&&e.status!=="registration"&&e.teams.includes(teamId)))fail("This roster is locked by a running competition.");}
function match(w:Workspace,event:Event,teams:string[],round:number,slot:number,at:string):Match {return {id:crypto.randomUUID(),eventId:event.id,teams,round,slot,scores:[],kills:[],status:"scheduled",evidence:"",note:"",winner:null,updatedAt:at};}
export function applyCommand(source:Workspace,command:Command,at=new Date().toISOString()):Workspace {
 const w=structuredClone(source), c=command, id=crypto.randomUUID();
 if(!c||typeof c.type!=="string")return fail("A valid action is required.");
 switch(c.type){
 case "configure": {
  const name=str(c.name,"Game name",80), modes=texts(c.modes,"Modes"),roles=texts(c.roles,"Roles");
  if(w.events.some(e=>!modes.includes(e.mode)))fail("Keep modes used by existing competitions.");
  if(w.players.some(p=>!roles.includes(p.role)))fail("Keep roles used by existing players.");
  w.rules={...w.rules,name,short:str(c.short,"Short name",8),modes,roles,rosterSize:num(c.rosterSize,1,20,"Roster size"),resultType:one(c.resultType,["series","placement"],"result type")}; break;
 }
 case "player.add": {
  const tag=str(c.tag,"Gamertag",60),uid=str(c.uid??"","Game UID",80,true);
  unique(w.players.map(p=>p.tag),tag,"Gamertag");if(uid)unique(w.players.filter(p=>p.uid).map(p=>p.uid),uid,"Game UID");
  w.players.push({id,tag,uid,role:one(c.role,w.rules.roles,"role"),country:str(c.country,"Country",60),age:one(c.age,["adult","minor","unknown"],"age group")});break;
 }
 case "team.add":{
  const name=str(c.name,"Squad name",80);unique(w.teams.map(t=>t.name),name,"Squad name");
  w.teams.push({id,name,tier:one(c.tier,["First team","Second team","Academy","Ranked grinders","Community"],"tier"),players:[]});break;
 }
 case "team.assign":{
  const team=found(w.teams,c.teamId,"Squad"),p=found(w.players,c.playerId,"Player");editableRoster(w,team.id);
  if(w.teams.some(t=>t.players.includes(p.id)))fail("Player already belongs to a squad. Use a transfer or remove them first.");
  if(team.players.length>=30)fail("Squads support at most 30 registered players.");team.players.push(p.id);break;
 }
 case "team.remove":{
  const team=found(w.teams,c.teamId,"Squad");editableRoster(w,team.id);if(!team.players.includes(String(c.playerId)))fail("Player is not in this squad.");
  team.players=team.players.filter(p=>p!==c.playerId);break;
 }
 case "event.add":{
  const format=one(c.format,["league","knockout","placement"],"format");
  const bestOf=num(c.bestOf,1,9,"Best of");if(bestOf%2!==1)fail("Best of must be an odd number.");
  if(typeof c.official!=="boolean")fail("Choose official or practice.");
  const pp=Array.isArray(c.placementPoints)?c.placementPoints:[15,12,10,8,6,4,2,1];if(pp.length<1||pp.length>64)fail("Enter 1–64 placement point values.");
  const points=pp.map(v=>num(v,0,1000,"Placement points"));if(points.some((v,i)=>i>0&&v>points[i-1]))fail("Placement points must decrease or stay equal.");
  w.events.push({id,name:str(c.name,"Competition name",100),mode:one(c.mode,w.rules.modes,"mode"),season:str(c.season,"Season",50),region:str(c.region,"Region",60),format,official:c.official,teamSize:num(c.teamSize,1,20,"Starting roster"),bestOf,winPoints:num(c.winPoints,1,10,"Win points"),placementPoints:points,killPoints:num(c.killPoints,0,100,"Kill points"),teams:[],status:"registration"});break;
 }
 case "event.entry":{
  const e=found(w.events,c.eventId,"Competition"),t=found(w.teams,c.teamId,"Squad");if(e.status!=="registration")fail("Registration is closed.");
  if(e.teams.includes(t.id))fail("Squad is already registered.");if(e.teams.length>=64)fail("A competition supports at most 64 squads.");
  if(t.players.length<e.teamSize)fail(`This competition requires at least ${e.teamSize} rostered players.`);
  e.teams.push(t.id);break;
 }
 case "event.start":{
  const e=found(w.events,c.eventId,"Competition");if(e.status!=="registration")fail("Competition has already started.");
  if(e.teams.length<2)fail("Register at least two squads.");
  if(e.teams.some(id=>found(w.teams,id,"Squad").players.length<e.teamSize))fail("One or more squads no longer meet the roster size.");
  if(e.format==="knockout"&&(e.teams.length&(e.teams.length-1))!==0)fail("Knockout brackets require 2, 4, 8, 16, 32 or 64 squads.");
  if(e.format==="league"&&e.teams.length>20)fail("League format supports at most 20 squads; split larger events into groups.");
  e.status="running";
  if(e.format==="league"){let slot=0;for(let i=0;i<e.teams.length;i++)for(let j=i+1;j<e.teams.length;j++)w.matches.push(match(w,e,[e.teams[i],e.teams[j]],1,slot++,at));}
  else if(e.format==="knockout"){for(let i=0;i<e.teams.length;i+=2)w.matches.push(match(w,e,e.teams.slice(i,i+2),1,i/2,at));}
  else w.matches.push(match(w,e,[...e.teams],1,0,at));break;
 }
 case "event.round":{
  const e=found(w.events,c.eventId,"Competition");if(e.format!=="placement"||e.status!=="running")fail("Only running placement competitions accept another round.");
  const rounds=w.matches.filter(m=>m.eventId===e.id);if(rounds.some(m=>m.status!=="approved"))fail("Approve the current round first.");
  w.matches.push(match(w,e,[...e.teams],rounds.length+1,0,at));break;
 }
 case "event.finish":{
  const e=found(w.events,c.eventId,"Competition");if(e.status!=="running"||e.format!=="placement")fail("Only running placement competitions can be closed manually.");
  if(w.matches.some(m=>m.eventId===e.id&&m.status!=="approved"))fail("Resolve and approve every round first.");e.status="complete";break;
 }
 case "match.submit":{
  const m=found(w.matches,c.matchId,"Match"),e=found(w.events,m.eventId,"Competition");
  if(e.status!=="running"||m.status==="approved")fail("An approved or closed match cannot be overwritten.");
  if(!Array.isArray(c.scores)||c.scores.length!==m.teams.length)fail("Enter a result for every entrant.");
  m.scores=c.scores.map(x=>num(x,0,e.format==="placement"?m.teams.length:e.bestOf,"Result"));
  if(e.format==="placement"){
   if(m.scores.some(s=>s<1)||new Set(m.scores).size!==m.teams.length)fail("Placements must be unique, from 1 to the number of entrants.");
   if(!Array.isArray(c.kills)||c.kills.length!==m.teams.length)fail("Enter eliminations for every entrant.");m.kills=c.kills.map(x=>num(x,0,500,"Eliminations"));m.winner=m.teams[m.scores.indexOf(1)];
  }else{
   const target=Math.ceil(e.bestOf/2);if(Math.max(...m.scores)!==target||Math.min(...m.scores)>=target)fail(`A best-of-${e.bestOf} series must finish with one squad on ${target} wins.`);
   m.winner=m.teams[m.scores[0]>m.scores[1]?0:1];
  }
  m.evidence=link(c.evidence);m.note=str(c.note??"","Result note",2000,true);m.status="submitted";m.updatedAt=at;break;
 }
 case "match.dispute":{
  const m=found(w.matches,c.matchId,"Match");if(m.status!=="submitted")fail("Only submitted results can be disputed. Approved records are locked.");
  m.note=str(c.note,"Dispute reason",2000);m.status="disputed";m.updatedAt=at;break;
 }
 case "match.approve":{
  const m=found(w.matches,c.matchId,"Match"),e=found(w.events,m.eventId,"Competition");if(m.status!=="submitted")fail("Submit or resolve the result before approval.");
  if(!m.evidence)fail("Attach a result evidence link before approval.");m.status="approved";m.updatedAt=at;
  const all=w.matches.filter(x=>x.eventId===e.id);
  if(e.format==="league"&&all.every(x=>x.status==="approved"))e.status="complete";
  if(e.format==="knockout"){
   const round=all.filter(x=>x.round===m.round).sort((a,b)=>a.slot-b.slot);
   if(round.every(x=>x.status==="approved")){
    if(round.length===1)e.status="complete";
    else for(let i=0;i<round.length;i+=2)w.matches.push(match(w,e,[round[i].winner!,round[i+1].winner!],m.round+1,i/2,at));
   }
  }break;
 }
 case "transfer.add":{
  const p=found(w.players,c.playerId,"Player"),to=found(w.teams,c.to,"Destination squad"),from=w.teams.find(t=>t.players.includes(p.id));
  if(!from)fail("Roster the player before proposing a transfer.");if(from.id===to.id)fail("Choose a different destination squad.");
  if(w.transfers.some(t=>t.playerId===p.id&&t.status==="proposed"))fail("This player already has a pending proposal.");
  w.transfers.push({id,playerId:p.id,from:from.id,to:to.id,kind:one(c.kind,["Permanent","Loan"],"transfer type"),note:str(c.note??"","Transfer note",2000,true),status:"proposed",consent:false});break;
 }
 case "transfer.resolve":{
  const t=found(w.transfers,c.transferId,"Transfer");if(t.status!=="proposed")fail("This proposal has already been resolved.");
  if(c.accept===false){t.status="rejected";break;}
  if(c.accept!==true||c.consent!==true)fail("Record the player's consent before completing this roster change.");
  const p=found(w.players,t.playerId,"Player");if(p.age!=="adult")fail("Transfers for minors or unconfirmed ages are blocked until a verified guardian-consent service is connected.");
  const from=found(w.teams,t.from,"Source squad"),to=found(w.teams,t.to,"Destination squad");editableRoster(w,from.id);editableRoster(w,to.id);
  if(!from.players.includes(p.id))fail("Player is no longer in the source squad.");if(to.players.length>=30)fail("Destination roster is full.");
  from.players=from.players.filter(id=>id!==p.id);to.players.push(p.id);t.status="completed";t.consent=true;break;
 }
 case "task.add":w.tasks.push({id,title:str(c.title,"Drill title",120),mode:one(c.mode,w.rules.modes,"mode"),notes:str(c.notes??"","Drill notes",4000,true),done:false,createdAt:at});break;
 case "task.toggle":{const t=found(w.tasks,c.taskId,"Drill");t.done=!t.done;break;}
 case "guide.add":w.guides.push({id,title:str(c.title,"Guide title",120),mode:one(c.mode,w.rules.modes,"mode"),notes:str(c.notes,"Guide notes",10000),url:link(c.url),updatedAt:at});break;
 case "room.add":{const t=found(w.teams,c.teamId,"Squad");w.room.push({id,teamId:t.id,text:str(c.text,"Room note",2000),at});break;}
 default:fail("Unknown workspace action.");
 }
 if([w.players,w.teams,w.events,w.matches,w.transfers,w.tasks,w.guides,w.room].some(a=>a.length>2000))fail("This workspace has reached its 2,000-record limit for this category. Export it before starting a new season workspace.");
 w.audit.unshift({id,at,action:c.type});w.audit=w.audit.slice(0,250);
 return w;
}
export type Standing = {teamId:string;played:number;wins:number;losses:number;points:number;difference:number};
export function standings(w:Workspace,eventId:string):Standing[]{
 const e=found(w.events,eventId,"Competition");const rows=new Map(e.teams.map(teamId=>[teamId,{teamId,played:0,wins:0,losses:0,points:0,difference:0}]));
 for(const m of w.matches.filter(m=>m.eventId===e.id&&m.status==="approved"))m.teams.forEach((id,i)=>{
  const r=rows.get(id)!;r.played++;if(m.winner===id)r.wins++;else r.losses++;
  if(e.format==="placement"){r.points+=(e.placementPoints[m.scores[i]-1]??0)+m.kills[i]*e.killPoints;r.difference+=m.kills[i];}
  else{r.points+=m.winner===id?e.winPoints:0;r.difference+=m.scores[i]-m.scores[1-i];}
 });
 return [...rows.values()].sort((a,b)=>b.points-a.points||b.wins-a.wins||b.difference-a.difference||a.teamId.localeCompare(b.teamId));
}
