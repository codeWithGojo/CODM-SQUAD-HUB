export const rankings = {
  MP:[
    {rank:1,team:'RAVEN ESPORTS',country:'Nigeria',region:'West Africa',rating:1842,form:'WWWWW',tier:'T1',delta:'+18'},
    {rank:2,team:'NIM ESPORTS',country:'Nigeria',region:'West Africa',rating:1796,form:'WWWLW',tier:'T1',delta:'+12'},
    {rank:3,team:'AXIS LEGION',country:'South Africa',region:'Southern Africa',rating:1721,form:'LWWWW',tier:'T1',delta:'-4'},
    {rank:4,team:'VANTA',country:'Ghana',region:'West Africa',rating:1614,form:'WLWWW',tier:'T2',delta:'+21'},
    {rank:5,team:'ONYX',country:'Kenya',region:'East Africa',rating:1555,form:'WWLLW',tier:'T2',delta:'+6'},
  ],
  BR:[
    {rank:1,team:'VANTA BR',country:'Ghana',region:'West Africa',rating:1911,form:'12131',tier:'T1',delta:'+24'},
    {rank:2,team:'RAVEN ROYALE',country:'Nigeria',region:'West Africa',rating:1867,form:'21321',tier:'T1',delta:'+8'},
    {rank:3,team:'AXIS BR',country:'South Africa',region:'Southern Africa',rating:1790,form:'34211',tier:'T1',delta:'+16'},
  ]
};

export const tournaments=[
 {id:'c1',name:'Carry1st Africa Championship',mode:'MP',tier:'MAJOR',status:'REGISTRATION',date:'AUG 28',teams:32,prize:'$60,000',weight:'1.00x',organizer:'Carry1st',verified:true},
 {id:'aer33',name:'AER Weekly 33',mode:'BR',tier:'COMMUNITY',status:'LIVE',date:'AUG 15',teams:18,prize:'₦100K / Gear',weight:'0.22x',organizer:'AER',verified:true},
 {id:'wam',name:'West Africa Masters',mode:'MP',tier:'REGIONAL',status:'UPCOMING',date:'SEP 04',teams:24,prize:'₦2,000,000',weight:'0.65x',organizer:'WAM League',verified:true},
];

export const scrims=[
 {team:'RAVEN ESPORTS',tier:'T1',region:'West Africa',country:'Nigeria',mode:'MP',format:'BO5',time:'20:00 WAT',maps:'HP • S&D • DOM',need:'T1–T2',whatsapp:'+234000000001'},
 {team:'VANTA',tier:'T2',region:'West Africa',country:'Ghana',mode:'MP',format:'BO3',time:'21:30 GMT',maps:'HP • S&D',need:'T2–T3',whatsapp:'+233000000002'},
 {team:'AXIS BR',tier:'T1',region:'Southern Africa',country:'South Africa',mode:'BR',format:'6 GAMES',time:'19:00 SAST',maps:'ISOLATED',need:'T1–T2',whatsapp:'+27000000003'},
];

export const freeAgents=[
 {name:'Ares',shid:'SH-000411',role:'SLAYER',mode:'MP',country:'Nigeria',tier:'T1',rating:1760,value:'₦230K',form:'9.1',status:'AVAILABLE'},
 {name:'Kairo',shid:'SH-000207',role:'FLEX',mode:'MP',country:'Ghana',tier:'T2',rating:1618,value:'₦145K',form:'8.5',status:'OPEN TO OFFERS'},
 {name:'Mako',shid:'SH-000922',role:'IGL',mode:'BR',country:'Kenya',tier:'T1',rating:1810,value:'₦205K',form:'8.9',status:'AVAILABLE'},
];

export const news=[
 {type:'TRANSFER',title:'NIM complete signing of Kairo',body:'The former Vanta flex joins NIM First Team after a negotiated permanent transfer.',time:'18 MIN',tag:'CONFIRMED'},
 {type:'RANKINGS',title:'Raven hold #1 after AER Week 32',body:'NIM close the gap after a 3–1 semi-final run. The top two are now separated by 46 rating points.',time:'1 HR',tag:'MP'},
 {type:'TOURNAMENT',title:'Carry1st Africa registration opens',body:'Verified organizations can register their locked rosters directly from the Tournament Hub.',time:'3 HR',tag:'MAJOR'},
];

export const playerHistory=[
 {date:'2026-08-01',title:'Promoted to NIM First Team',type:'PROMOTION',detail:'T3 Academy → T1 First Team'},
 {date:'2026-07-26',title:'AER Weekly 31 — Champion',type:'TROPHY',detail:'NIM Academy • MP'},
 {date:'2026-06-14',title:'Joined NIM Academy',type:'TRANSFER',detail:'Free transfer'},
 {date:'2025-11-03',title:'Competitive debut',type:'CAREER',detail:'West Africa community league'},
];
