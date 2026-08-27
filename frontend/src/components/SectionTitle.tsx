import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { colors } from '../theme/colors';

export function SectionTitle({ title, action }: { title: string; action?: string }) {
  return <View style={s.row}><Text style={s.title}>{title}</Text>{action ? <Pressable><Text style={s.action}>{action}</Text></Pressable> : null}</View>;
}
const s = StyleSheet.create({
  row:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',marginBottom:10},
  title:{color:colors.white,fontSize:14,fontWeight:'600'},
  action:{color:colors.redBright,fontSize:11,fontWeight:'600'},
});
