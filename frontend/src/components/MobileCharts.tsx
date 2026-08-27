import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

export function RingGauge({value,label,size=118}:{value:string|number;label:string;size?:number}){
  return <View style={[s.ring,{width:size,height:size,borderRadius:size/2}]}>
    <View style={[s.ringInner,{width:size-22,height:size-22,borderRadius:(size-22)/2}]}>
      <Text style={s.ringValue}>{value}</Text>
      <Text style={s.ringLabel}>{label}</Text>
    </View>
  </View>
}

export function SparkLine({compact=false}:{compact?:boolean}){
  const h=compact?54:82;
  return <View style={[s.spark,{height:h}]}>
    <View style={[s.gridLine,{top:'25%'}]}/><View style={[s.gridLine,{top:'50%'}]}/><View style={[s.gridLine,{top:'75%'}]}/>
    <View style={[s.seg,{left:'3%',bottom:'25%',width:'18%',transform:[{rotate:'-10deg'}]}]}/>
    <View style={[s.seg,{left:'20%',bottom:'31%',width:'18%',transform:[{rotate:'17deg'}]}]}/>
    <View style={[s.seg,{left:'36%',bottom:'21%',width:'20%',transform:[{rotate:'-24deg'}]}]}/>
    <View style={[s.seg,{left:'53%',bottom:'40%',width:'18%',transform:[{rotate:'8deg'}]}]}/>
    <View style={[s.seg,{left:'69%',bottom:'37%',width:'15%',transform:[{rotate:'-23deg'}]}]}/>
    <View style={[s.seg,{left:'81%',bottom:'51%',width:'15%',transform:[{rotate:'8deg'}]}]}/>
    {['4%','20%','36%','54%','70%','83%','95%'].map((left,i)=><View key={left} style={[s.point,{left,bottom:[22,29,19,39,35,49,53][i]+'%'}]}/>) }
  </View>
}

export function MicroBars(){
  return <View style={s.bars}>{[26,44,35,58,71,52,78].map((height,i)=><View key={i} style={[s.bar,{height}]}/>)}</View>
}

const s=StyleSheet.create({
  ring:{borderWidth:10,borderColor:'#332044',borderTopColor:colors.magenta,borderRightColor:colors.violet,borderBottomColor:'#7A2AF6',alignItems:'center',justifyContent:'center',backgroundColor:'#0A0C13',shadowColor:colors.magenta,shadowOpacity:.22,shadowRadius:12,elevation:4},
  ringInner:{backgroundColor:'#0B0E16',alignItems:'center',justifyContent:'center',borderWidth:1,borderColor:'#2B2440'},
  ringValue:{color:colors.white,fontSize:25,fontWeight:'800',letterSpacing:-.7},
  ringLabel:{color:colors.subtle,fontSize:7,fontWeight:'700',letterSpacing:1,marginTop:2},
  spark:{position:'relative',overflow:'hidden'},
  gridLine:{position:'absolute',left:0,right:0,height:1,backgroundColor:'#1B2130'},
  seg:{position:'absolute',height:3,borderRadius:3,backgroundColor:colors.magenta,shadowColor:colors.magenta,shadowOpacity:.45,shadowRadius:4,elevation:2},
  point:{position:'absolute',width:7,height:7,borderRadius:7,backgroundColor:'#F2A7FF',borderWidth:2,borderColor:colors.magenta},
  bars:{height:84,flexDirection:'row',gap:7,alignItems:'flex-end'},
  bar:{flex:1,borderRadius:4,backgroundColor:'#34284C',borderTopWidth:2,borderTopColor:colors.magenta},
});
