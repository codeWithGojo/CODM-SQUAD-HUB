import React from 'react';
import { View,Text,StyleSheet,Pressable } from 'react-native';
import { colors } from '../theme/colors';
import { MainTab } from '../types/navigation';

const tabs:[MainTab,string,string][]=[['HOME','⌂','Home'],['COMPETE','♜','Compete'],['HUB','◎','Hub'],['CAREER','◇','Career'],['MORE','≡','More']];

export function BottomNav({active,onChange}:{active:MainTab;onChange:(t:MainTab)=>void}){
  return <View style={s.wrap}>{tabs.map(([k,ic,l])=>{const on=active===k;return <Pressable key={k} onPress={()=>onChange(k)} style={s.item}>
    <View style={[s.iconWrap,on&&s.iconOn]}><Text style={[s.icon,on&&s.on]}>{ic}</Text></View>
    <Text style={[s.label,on&&s.on]}>{l}</Text>
    {on?<View style={s.dot}/>:null}
  </Pressable>})}</View>
}

const s=StyleSheet.create({
  wrap:{height:72,flexDirection:'row',backgroundColor:'#080A10',borderTopWidth:1,borderTopColor:'#1E2332',paddingTop:4,paddingBottom:7},
  item:{flex:1,alignItems:'center',justifyContent:'center',position:'relative'},
  iconWrap:{width:42,height:30,alignItems:'center',justifyContent:'center',borderRadius:10},
  iconOn:{backgroundColor:'#25113A',borderWidth:1,borderColor:'#5C277F'},
  icon:{color:'#697084',fontSize:16,fontWeight:'700'},
  label:{color:'#697084',fontSize:9,fontWeight:'600',marginTop:3},
  on:{color:'#F3E8FF',fontWeight:'700'},
  dot:{position:'absolute',bottom:2,width:4,height:4,borderRadius:4,backgroundColor:colors.magenta,shadowColor:colors.magenta,shadowOpacity:.8,shadowRadius:3}
});
