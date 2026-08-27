import React from 'react';
import { Text, StyleSheet, View } from 'react-native';
import { colors } from '../theme/colors';
export function Badge({ text, tone='red' }:{text:string;tone?:'red'|'neutral'|'green'}){
  const bg = tone==='green' ? '#10261B' : tone==='neutral' ? colors.surface3 : colors.redSoft;
  const fg = tone==='green' ? colors.success : tone==='neutral' ? '#C4C6CC' : colors.redBright;
  return <View style={[s.box,{backgroundColor:bg}]}><Text style={[s.text,{color:fg}]}>{text}</Text></View>;
}
const s=StyleSheet.create({box:{paddingHorizontal:8,paddingVertical:4,borderRadius:6,alignSelf:'flex-start'},text:{fontSize:10,fontWeight:'600',letterSpacing:.7}});
