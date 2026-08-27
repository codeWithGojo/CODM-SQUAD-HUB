export type IspCoverage = {name:string; type:string; states:string[]; note:string};
export const nigeriaStates = ['Lagos','Abuja (FCT)','Oyo','Osun','Rivers','Delta','Edo','Ogun','Kwara','Enugu','Anambra','Kaduna','Kano','Plateau'];
export const ispCoverage:IspCoverage[] = [
  {name:'MTN Nigeria',type:'Mobile / 5G',states:nigeriaStates,note:'Broad national mobile coverage; 5G concentrated in major cities.'},
  {name:'Airtel Nigeria',type:'Mobile / 5G',states:nigeriaStates,note:'Broad mobile coverage with strong urban LTE footprint.'},
  {name:'Glo',type:'Mobile / 4G',states:nigeriaStates,note:'National mobile footprint; local performance varies heavily.'},
  {name:'9mobile',type:'Mobile / 4G',states:['Lagos','Abuja (FCT)','Oyo','Osun','Rivers','Delta','Edo','Ogun','Kwara','Enugu','Anambra','Kaduna','Kano'],note:'Urban-first footprint; verify locally before relying on it for tournament play.'},
  {name:'Spectranet',type:'Fixed LTE / Fiber',states:['Lagos','Abuja (FCT)','Oyo','Ogun'],note:'Primarily selected urban areas.'},
  {name:'Smile',type:'Fixed / Mobile LTE',states:['Lagos','Abuja (FCT)','Oyo','Rivers','Ogun'],note:'Selected metro coverage; availability can be neighborhood-specific.'},
  {name:'FiberOne',type:'Fiber',states:['Lagos','Abuja (FCT)','Ogun'],note:'Fiber availability depends on estate/street coverage.'},
];
