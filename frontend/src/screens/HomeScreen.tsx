import React,{useEffect,useRef,useState} from 'react';
import { Animated,ScrollView,View,Text,StyleSheet,Pressable,useWindowDimensions } from 'react-native';
import { colors } from '../theme/colors';
import { DetailRoute } from '../types/navigation';
import { RingGauge,SparkLine } from '../components/MobileCharts';

const featured=[
  {name:'Africa Legends Showdown',time:'07:45:24',blurb:'Top MP squads battle for regional points.',slots:'19/24',cost:'10,000 pts',tone:'#5B16D7'},
  {name:'Sweat & Glory Cup',time:'12:25:59',blurb:'High-pressure BO5 bracket for verified teams.',slots:'19/24',cost:'Free',tone:'#A015D9'},
  {name:'CoDM Weekend Warzone',time:'35:20:06',blurb:'Weekend battles, live brackets and squad rewards.',slots:'18/24',cost:'5,000 pts',tone:'#4338CA'},
  {name:'Clan Domination League',time:'04:33:46',blurb:'League play with verified roster locks.',slots:'22/24',cost:'Free',tone:'#7A136D'},
];

function CountUp({to,suffix=''}:{to:number;suffix?:string}){
  const[v,setV]=useState(0);
  useEffect(()=>{let i=0;const total=28;const id=setInterval(()=>{i++;setV(Math.round(to*i/total));if(i>=total)clearInterval(id)},30);return()=>clearInterval(id)},[to]);
  return <Text style={s.statValue}>{v.toLocaleString()}{suffix}</Text>
}

function MiniOperator({mini=false}:{mini?:boolean}){return <View style={[s.operatorWrap,mini&&s.operatorWrapMini]}><View style={[s.operatorGlow,mini&&s.operatorGlowMini]}/><View style={[s.operatorHead,mini&&s.operatorHeadMini]}><View style={s.visor}/></View><View style={[s.operatorBody,mini&&s.operatorBodyMini]}/><View style={[s.operatorShoulder,mini&&s.operatorShoulderMini]}/></View>}

export function HomeScreen({open}:{open:(r:DetailRoute)=>void}){
  const {width}=useWindowDimensions();
  const compact=width<390;
  const scrollY=useRef(new Animated.Value(0)).current;
  return <Animated.ScrollView
    contentContainerStyle={s.content}
    showsVerticalScrollIndicator={false}
    onScroll={Animated.event([{nativeEvent:{contentOffset:{y:scrollY}}}],{useNativeDriver:true})}
    scrollEventThrottle={16}>

    <View style={s.greetingRow}>
      <View><Text style={s.morning}>Good morning,</Text><Text style={s.user}>Favour</Text><Text style={s.userMeta}>T1 competitor · West Africa</Text></View>
      <Pressable onPress={()=>open('PLAYER_PASSPORT')} style={s.avatar}><Text style={s.avatarT}>F</Text><View style={s.online}/></Pressable>
    </View>

    <View style={s.hero}>
      <Animated.View style={[s.heroGlowOne,{transform:[{translateY:scrollY.interpolate({inputRange:[0,240],outputRange:[0,25],extrapolate:'clamp'})}]}]}/>
      <View style={s.heroGlowTwo}/><View style={s.heroGrid}/>
      <MiniOperator/>
      <View style={s.heroCopy}>
        <View style={s.membersPill}><Text style={s.membersPillT}>●  345 members</Text></View>
        <Text style={[s.heroTitle,compact&&{fontSize:28}]}>COMPETE IN{`\n`}CODM SQUAD HUB{`\n`}<Text style={s.heroAccent}>TOURNAMENTS</Text></Text>
        <Text style={s.heroSub}>Verified events, official rankings and a competitive record that follows your career.</Text>
        <Pressable onPress={()=>open('TOURNAMENT_CONTROL')} style={s.heroBtn}><Text style={s.heroBtnT}>Explore tournaments</Text><Text style={s.heroBtnArrow}>›</Text></Pressable>
      </View>
      <View style={s.heroStats}>
        <View style={s.heroStat}><CountUp to={345}/><Text style={s.statLabel}>Members</Text></View>
        <View style={s.heroStat}><CountUp to={3200}/><Text style={s.statLabel}>Matches</Text></View>
        <View style={s.heroStat}><CountUp to={235}/><Text style={s.statLabel}>Tournaments</Text></View>
      </View>
    </View>

    <View style={s.quickRow}>
      {[
        ['⌁','Connection','CONNECTION_CHECK'],['♜','Rankings','RANKINGS'],['⚔','Scrims','SCRIM_FINDER'],['◇','Passport','PLAYER_PASSPORT']
      ].map(([icon,label,route])=><Pressable key={label} onPress={()=>open(route as DetailRoute)} style={s.quick}><View style={s.quickIcon}><Text style={s.quickIconT}>{icon}</Text></View><Text style={s.quickT}>{label}</Text></Pressable>)}
    </View>

    <View style={s.sectionHead}><View><Text style={s.sectionTitle}>Featured tournaments</Text><Text style={s.sectionSub}>Verified events open for registration.</Text></View><Pressable onPress={()=>open('TOURNAMENT_CONTROL')}><Text style={s.link}>View all</Text></Pressable></View>
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.tournamentRow} snapToInterval={294} decelerationRate="fast">
      {featured.map((t,i)=><Pressable key={t.name} onPress={()=>open('TOURNAMENT_CONTROL')} style={({pressed})=>[s.tCard,pressed&&{transform:[{scale:.985}]}]}>
        <View style={[s.thumb,{backgroundColor:t.tone}]}>
          <View style={s.thumbGlow}/><View style={s.thumbGrid}/>
          <Text style={s.timer}>◉ {t.time}</Text><MiniOperator mini/><Text style={s.thumbLabel}>CODM AFRICA · {i%2===0?'MP':'BR'}</Text>
        </View>
        <View style={s.tBody}><Text style={s.tName}>{t.name}</Text><Text style={s.tBlurb}>{t.blurb}</Text>
          <View style={s.tActions}><View style={s.cost}><Text style={s.costT}>{t.cost}</Text></View><View style={s.join}><Text style={s.joinT}>Join</Text></View></View>
          <View style={s.tFoot}><Text style={s.avatarDots}>● ● ● ● <Text style={s.plus}>+{i+7}</Text></Text><Text style={s.slots}>{t.slots} Slots</Text></View>
        </View>
      </Pressable>)}
    </ScrollView>

    <View style={s.sectionHead}><View><Text style={s.sectionTitle}>Your season</Text><Text style={s.sectionSub}>A quick read on form, impact and activity.</Text></View><Pressable onPress={()=>open('PERFORMANCE')}><Text style={s.link}>Open lab</Text></Pressable></View>
    <View style={s.dashboardGrid}>
      <Pressable onPress={()=>open('PLAYER_PASSPORT')} style={[s.widget,s.ratingCard]}>
        <Text style={s.widgetKicker}>Player rating</Text><RingGauge value="78.4" label="RATING" size={112}/><Text style={s.widgetNote}>Elite squad · top 18%</Text>
      </Pressable>
      <View style={[s.widget,s.performanceCard]}><View style={s.widgetHeader}><View><Text style={s.widgetTitle}>Game statistic</Text><Text style={s.widgetSub}>Last 7 comp matches</Text></View><Text style={s.menuDots}>•••</Text></View><SparkLine/><View style={s.chartLegend}><Text style={s.legend}>● Rating</Text><Text style={s.legendAlt}>● Win impact</Text></View></View>
    </View>

    <View style={s.metricGrid}>
      {[
        ['1.28','K/D','+0.11'],['18','MVPs','+3'],['62%','Win rate','+5%'],['4.8K','Avg damage','+240']
      ].map(([v,l,d])=><View key={l} style={s.metric}><Text style={s.metricV}>{v}</Text><Text style={s.metricL}>{l}</Text><Text style={s.metricD}>↗ {d}</Text></View>)}
    </View>

    <View style={s.sectionHead}><View><Text style={s.sectionTitle}>Scene pulse</Text><Text style={s.sectionSub}>Updates without leaving the competitive hub.</Text></View><Pressable onPress={()=>open('NEWS')}><Text style={s.link}>News</Text></Pressable></View>
    <View style={s.newsRow}>
      <Pressable onPress={()=>open('NEWS')} style={[s.newsCard,s.newsDark]}><Text style={s.newsKicker}>NEW UPDATE</Text><Text style={s.newsTitle}>S6{`\n`}African Frontline</Text><Text style={s.newsCopy}>Maps, balance changes and event systems.</Text><Text style={s.link}>See what's new →</Text></Pressable>
      <Pressable onPress={()=>open('NEWS')} style={[s.newsCard,s.newsPurple]}><Text style={s.newsKicker}>LATEST NEWS</Text><Text style={s.newsTitle}>Carry1st registration is open.</Text><Text style={s.newsCopy}>Verified orgs can lock rosters directly in Squad Hub.</Text><Text style={s.linkLight}>Read story →</Text></Pressable>
    </View>

    <Pressable onPress={()=>open('CONNECTION_CHECK')} style={s.connectionBanner}>
      <View style={s.connectionIcon}><Text style={s.connectionIconT}>⌁</Text></View><View style={{flex:1}}><Text style={s.connectionTitle}>Connection Check</Text><Text style={s.connectionCopy}>Test ping, check ISP coverage and see what your connection means for comp.</Text></View><Text style={s.connectionArrow}>›</Text>
    </Pressable>
  </Animated.ScrollView>
}

const s=StyleSheet.create({
  content:{paddingHorizontal:14,paddingTop:14,paddingBottom:30,backgroundColor:colors.bg},
  greetingRow:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',marginBottom:14},morning:{color:colors.muted,fontSize:11,fontWeight:'500'},user:{color:colors.white,fontSize:22,fontWeight:'800',letterSpacing:-.5,marginTop:1},userMeta:{color:colors.subtle,fontSize:9,fontWeight:'600',marginTop:2},avatar:{width:46,height:46,borderRadius:13,backgroundColor:'#151326',borderWidth:1,borderColor:'#55307A',alignItems:'center',justifyContent:'center',position:'relative'},avatarT:{color:'#fff',fontSize:18,fontWeight:'800'},online:{position:'absolute',right:-1,bottom:2,width:10,height:10,borderRadius:10,backgroundColor:colors.success,borderWidth:2,borderColor:colors.bg},
  hero:{height:410,borderRadius:18,overflow:'hidden',backgroundColor:'#0A0714',borderWidth:1,borderColor:'#3A1E59',position:'relative',shadowColor:'#9C2CFF',shadowOpacity:.18,shadowRadius:18,elevation:5},heroGlowOne:{position:'absolute',width:330,height:330,borderRadius:200,backgroundColor:'#6516A0',opacity:.42,right:-80,top:-75},heroGlowTwo:{position:'absolute',width:230,height:230,borderRadius:150,backgroundColor:'#D11CFF',opacity:.16,right:40,top:40},heroGrid:{position:'absolute',top:0,left:0,right:0,bottom:0,borderWidth:1,borderColor:'rgba(255,255,255,.02)'},heroCopy:{padding:18,paddingRight:72,zIndex:3},membersPill:{alignSelf:'flex-start',backgroundColor:'rgba(106,38,160,.28)',borderWidth:1,borderColor:'#593278',borderRadius:8,paddingHorizontal:9,paddingVertical:6},membersPillT:{color:'#D9C4EF',fontSize:8,fontWeight:'700'},heroTitle:{color:'#fff',fontSize:31,fontWeight:'900',letterSpacing:-1.5,lineHeight:30,marginTop:15},heroAccent:{color:colors.magenta},heroSub:{color:'#B9B4C5',fontSize:10.5,lineHeight:15,marginTop:12,maxWidth:260},heroBtn:{height:38,alignSelf:'flex-start',paddingHorizontal:13,borderRadius:8,backgroundColor:'#8A1CDB',flexDirection:'row',alignItems:'center',gap:8,marginTop:14,shadowColor:colors.magenta,shadowOpacity:.3,shadowRadius:8,elevation:3},heroBtnT:{color:'#fff',fontSize:10,fontWeight:'800'},heroBtnArrow:{color:'#fff',fontSize:19,lineHeight:19},heroStats:{position:'absolute',left:12,right:12,bottom:12,flexDirection:'row',backgroundColor:'rgba(10,8,22,.87)',borderWidth:1,borderColor:'#39284E',borderRadius:11,paddingVertical:10,paddingHorizontal:5,zIndex:4},heroStat:{flex:1,alignItems:'center',borderRightWidth:1,borderRightColor:'#2D243B'},statValue:{color:'#fff',fontSize:16,fontWeight:'800'},statLabel:{color:'#8C859A',fontSize:7.5,fontWeight:'600',marginTop:2},operatorWrap:{position:'absolute',right:-18,top:76,width:162,height:240,zIndex:2},operatorWrapMini:{right:8,top:20,width:110,height:130,transform:[{scale:.72}]},operatorGlowMini:{top:8,right:0},operatorHeadMini:{top:4,right:32},operatorBodyMini:{top:55,right:10},operatorShoulderMini:{top:68,right:0},operatorGlow:{position:'absolute',width:150,height:150,borderRadius:100,backgroundColor:'#B523FF',opacity:.16,top:26,right:5},operatorHead:{position:'absolute',width:55,height:58,borderRadius:18,backgroundColor:'#151522',borderWidth:2,borderColor:'#633587',top:8,right:50,transform:[{rotate:'-5deg'}]},visor:{position:'absolute',width:35,height:11,borderRadius:7,backgroundColor:'#D128FF',left:9,top:19,shadowColor:colors.magenta,shadowOpacity:.8,shadowRadius:7,elevation:4},operatorBody:{position:'absolute',width:108,height:154,borderTopLeftRadius:42,borderTopRightRadius:35,backgroundColor:'#10111A',borderWidth:2,borderColor:'#312941',top:61,right:23,transform:[{rotate:'4deg'}]},operatorShoulder:{position:'absolute',width:128,height:42,borderRadius:20,backgroundColor:'#171723',top:77,right:8,transform:[{rotate:'-8deg'}]},
  quickRow:{flexDirection:'row',gap:8,marginTop:12},quick:{flex:1,backgroundColor:'#0E1119',borderWidth:1,borderColor:'#202538',borderRadius:11,paddingVertical:9,alignItems:'center'},quickIcon:{width:30,height:30,borderRadius:9,backgroundColor:'#25113A',alignItems:'center',justifyContent:'center'},quickIconT:{color:colors.magenta,fontSize:15,fontWeight:'800'},quickT:{color:colors.text,fontSize:8,fontWeight:'700',marginTop:6},
  sectionHead:{flexDirection:'row',alignItems:'flex-end',justifyContent:'space-between',marginTop:22,marginBottom:10},sectionTitle:{color:colors.white,fontSize:17,fontWeight:'800',letterSpacing:-.3},sectionSub:{color:colors.subtle,fontSize:9,marginTop:2},link:{color:colors.magenta,fontSize:9,fontWeight:'800'},linkLight:{color:'#fff',fontSize:9,fontWeight:'800'},
  tournamentRow:{gap:10,paddingRight:14},tCard:{width:284,backgroundColor:'#0E111A',borderWidth:1,borderColor:'#24293A',borderRadius:14,overflow:'hidden'},thumb:{height:138,position:'relative',overflow:'hidden'},thumbGlow:{position:'absolute',width:170,height:170,borderRadius:100,backgroundColor:'#E526FF',opacity:.16,right:-25,top:-40},thumbGrid:{position:'absolute',top:0,left:0,right:0,bottom:0,borderWidth:1,borderColor:'rgba(255,255,255,.03)'},timer:{position:'absolute',left:10,top:9,zIndex:5,color:'#FFE6FF',fontSize:8,fontWeight:'800',backgroundColor:'rgba(34,5,43,.72)',borderWidth:1,borderColor:'#C12FE4',paddingHorizontal:8,paddingVertical:5,borderRadius:7},thumbLabel:{position:'absolute',left:11,bottom:9,color:'#fff',fontSize:8,fontWeight:'800',letterSpacing:.7,zIndex:5},tBody:{padding:12},tName:{color:'#fff',fontSize:13,fontWeight:'800'},tBlurb:{color:colors.muted,fontSize:9,lineHeight:13,marginTop:4,minHeight:26},tActions:{flexDirection:'row',gap:8,marginTop:11},cost:{flex:1,height:34,borderRadius:7,backgroundColor:'#F0B92F',alignItems:'center',justifyContent:'center'},costT:{color:'#15120B',fontSize:8.5,fontWeight:'900'},join:{flex:1,height:34,borderRadius:7,backgroundColor:'#8C1DE0',alignItems:'center',justifyContent:'center'},joinT:{color:'#fff',fontSize:9,fontWeight:'800'},tFoot:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',borderTopWidth:1,borderTopColor:'#202537',marginTop:11,paddingTop:9},avatarDots:{color:'#D9C2FF',fontSize:9},plus:{color:colors.magenta},slots:{color:colors.muted,fontSize:9,fontWeight:'700'},
  dashboardGrid:{gap:10},widget:{backgroundColor:'#0E111A',borderWidth:1,borderColor:'#242A3A',borderRadius:14,padding:14},ratingCard:{alignItems:'center'},performanceCard:{minHeight:155},widgetKicker:{alignSelf:'flex-start',color:colors.subtle,fontSize:8,fontWeight:'800',letterSpacing:1.2,marginBottom:9},widgetNote:{color:colors.muted,fontSize:9,fontWeight:'600',marginTop:8},widgetHeader:{flexDirection:'row',justifyContent:'space-between'},widgetTitle:{color:'#fff',fontSize:14,fontWeight:'800'},widgetSub:{color:colors.subtle,fontSize:8.5,marginTop:2},menuDots:{color:colors.subtle,fontSize:13},chartLegend:{flexDirection:'row',gap:12,marginTop:5},legend:{color:colors.magenta,fontSize:8,fontWeight:'700'},legendAlt:{color:'#7A86FF',fontSize:8,fontWeight:'700'},
  metricGrid:{flexDirection:'row',flexWrap:'wrap',gap:8,marginTop:10},metric:{width:'48.8%',backgroundColor:'#0E111A',borderWidth:1,borderColor:'#242A3A',borderRadius:12,padding:13},metricV:{color:'#fff',fontSize:22,fontWeight:'800',letterSpacing:-.5},metricL:{color:colors.muted,fontSize:8,fontWeight:'700',marginTop:3},metricD:{color:colors.success,fontSize:8,fontWeight:'800',marginTop:8},
  newsRow:{gap:9},newsCard:{borderRadius:14,padding:15,minHeight:145,overflow:'hidden'},newsDark:{backgroundColor:'#10131B',borderWidth:1,borderColor:'#242A3A'},newsPurple:{backgroundColor:'#4B1978',borderWidth:1,borderColor:'#7D35A9'},newsKicker:{color:'#EFC9FF',fontSize:8,fontWeight:'900',letterSpacing:1.2},newsTitle:{color:'#fff',fontSize:20,fontWeight:'800',lineHeight:21,marginTop:9,maxWidth:260},newsCopy:{color:'#C1B8CB',fontSize:9,lineHeight:13,marginTop:8,maxWidth:270},
  connectionBanner:{marginTop:18,backgroundColor:'#110E1D',borderWidth:1,borderColor:'#5E2B83',borderRadius:14,padding:13,flexDirection:'row',alignItems:'center',gap:10},connectionIcon:{width:42,height:42,borderRadius:12,backgroundColor:'#28113A',alignItems:'center',justifyContent:'center'},connectionIconT:{color:colors.magenta,fontSize:20,fontWeight:'800'},connectionTitle:{color:'#fff',fontSize:12,fontWeight:'800'},connectionCopy:{color:colors.muted,fontSize:8.5,lineHeight:12,marginTop:3},connectionArrow:{color:colors.magenta,fontSize:24}
});
