export type GameRules = {
  id: string; name: string; short: string; color: string;
  modes: string[]; roles: string[]; rosterSize: number;
  resultType: "series" | "placement";
};
// Editable event templates, not claims about a publisher's current official rules.
export const GAMES: GameRules[] = [
  {id:"codm",name:"Call of Duty: Mobile",short:"CODM",color:"#c9ff4a",modes:["Multiplayer","Battle Royale"],roles:["OBJ","Slayer","Anchor","Flex","Sniper","IGL"],rosterSize:5,resultType:"series"},
  {id:"pubg-mobile",name:"PUBG Mobile",short:"PUBGM",color:"#f6c85f",modes:["Squads","Duos","Solo"],roles:["IGL","Assaulter","Support","Scout"],rosterSize:4,resultType:"placement"},
  {id:"free-fire",name:"Free Fire",short:"FF",color:"#ffa66b",modes:["Battle Royale","Clash Squad"],roles:["Rusher","Support","Sniper","IGL"],rosterSize:4,resultType:"placement"},
  {id:"valorant",name:"VALORANT",short:"VAL",color:"#ff8791",modes:["Standard"],roles:["Duelist","Initiator","Controller","Sentinel","IGL"],rosterSize:5,resultType:"series"},
  {id:"cs2",name:"Counter-Strike 2",short:"CS2",color:"#f5c96b",modes:["Competitive"],roles:["IGL","Entry","AWPer","Lurker","Support"],rosterSize:5,resultType:"series"},
  {id:"mlbb",name:"Mobile Legends: Bang Bang",short:"MLBB",color:"#96baff",modes:["Standard"],roles:["EXP lane","Gold lane","Mid lane","Jungle","Roam"],rosterSize:5,resultType:"series"},
  {id:"ea-fc",name:"EA SPORTS FC",short:"FC",color:"#a0edc2",modes:["1v1","2v2","Clubs"],roles:["Competitor","Captain"],rosterSize:1,resultType:"series"},
  {id:"rocket-league",name:"Rocket League",short:"RL",color:"#8ac9ff",modes:["3v3","2v2","1v1"],roles:["First man","Second man","Third man"],rosterSize:3,resultType:"series"},
];
export function defaultGame(id: string): GameRules {
  const preset = GAMES.find(game => game.id === id);
  if (preset) return structuredClone(preset);
  if (/^custom-[a-f0-9-]{36}$/.test(id)) return {id,name:"New esports game",short:"NEW",color:"#c9ff4a",modes:["Standard"],roles:["Competitor"],rosterSize:5,resultType:"series"};
  throw new Error("Unknown game. Choose a game from the selector.");
}
