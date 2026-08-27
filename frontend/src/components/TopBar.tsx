import React from 'react';
import { View,Text,StyleSheet,Pressable } from 'react-native';
import { colors } from '../theme/colors';

export function TopBar({onNotifications}:{onNotifications?:()=>void}){
  return <View style={s.wrap}>
    <View style={s.brandRow}>
      <View style={s.mark}><View style={s.markCore}/></View>
      <View>
        <Text style={s.brand}>CoDM <Text style={s.accent}>Squad Hub</Text></Text>
        <Text style={s.sub}>African competitive network</Text>
      </View>
    </View>
    <View style={s.actions}>
      <Pressable style={s.iconBtn}><Text style={s.icon}>⌕</Text></Pressable>
      <Pressable onPress={onNotifications} style={s.iconBtn}><Text style={s.icon}>●</Text><View style={s.dot}/></Pressable>
    </View>
  </View>
}

const s=StyleSheet.create({
  wrap:{height:62,flexDirection:'row',alignItems:'center',justifyContent:'space-between',borderBottomWidth:1,borderBottomColor:'#1C2030',paddingHorizontal:14,backgroundColor:'#080A10'},
  brandRow:{flexDirection:'row',alignItems:'center',gap:10},
  mark:{width:34,height:34,borderRadius:10,backgroundColor:'#25123C',borderWidth:1,borderColor:'#6F2DA8',alignItems:'center',justifyContent:'center',shadowColor:colors.magenta,shadowOpacity:.28,shadowRadius:7,elevation:3},
  markCore:{width:14,height:14,transform:[{rotate:'45deg'}],backgroundColor:colors.magenta,borderWidth:3,borderColor:'#DCA8FF'},
  brand:{color:colors.white,fontWeight:'800',fontSize:15,letterSpacing:-.3},accent:{color:colors.magenta},
  sub:{color:colors.subtle,fontWeight:'500',fontSize:9,marginTop:1},
  actions:{flexDirection:'row',gap:7},
  iconBtn:{width:34,height:34,borderRadius:9,backgroundColor:'#10131D',borderWidth:1,borderColor:'#202536',alignItems:'center',justifyContent:'center',position:'relative'},
  icon:{color:colors.muted,fontSize:14,fontWeight:'700'},
  dot:{position:'absolute',width:7,height:7,borderRadius:7,backgroundColor:colors.magenta,right:5,top:5,borderWidth:2,borderColor:'#10131D'}
});
