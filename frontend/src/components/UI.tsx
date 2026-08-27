import React from 'react';
import { View, Text, StyleSheet, Pressable, TextInput } from 'react-native';
import { colors } from '../theme/colors';

export function SectionHeader({title,action,onAction}:{title:string;action?:string;onAction?:()=>void}){
  return <View style={s.sectionRow}><Text style={s.sectionTitle}>{title}</Text>{action?<Pressable onPress={onAction}><Text style={s.action}>{action}</Text></Pressable>:null}</View>;
}

export function Pill({text,tone='dark'}:{text:string;tone?:'red'|'dark'|'green'|'gold'|'blue'}){
  const toneMap:any={red:[colors.redSoft,'#E4B6FF'],dark:[colors.surface3,colors.muted],green:['#153526','#6BE0A0'],gold:['#3A2E18','#F6C85F'],blue:['#183246','#6CC7FF']};
  const [bg,fg]=toneMap[tone];
  return <View style={[s.pill,{backgroundColor:bg}]}><Text style={[s.pillText,{color:fg}]}>{text}</Text></View>;
}

export function Metric({value,label,accent}:{value:string,label:string,accent?:boolean}){
  return <View style={s.metric}><Text style={[s.metricValue,accent&&{color:colors.redBright}]}>{value}</Text><Text style={s.metricLabel}>{label}</Text></View>
}

export function ActionButton({label,onPress,secondary=false,small=false}:{label:string;onPress?:()=>void;secondary?:boolean;small?:boolean}){
  return <Pressable onPress={onPress} style={[s.btn,secondary&&s.btnSecondary,small&&s.btnSmall]}><Text style={[s.btnText,secondary&&s.btnTextSecondary]}>{label}</Text></Pressable>
}

export function SearchBox({value,onChange,placeholder='Search'}:{value:string;onChange:(v:string)=>void;placeholder?:string}){
  return <View style={s.search}><Text style={s.searchIcon}>⌕</Text><TextInput value={value} onChangeText={onChange} placeholder={placeholder} placeholderTextColor={colors.subtle} style={s.searchInput}/></View>
}

export function EmptyState({title,copy}:{title:string;copy:string}){
  return <View style={s.empty}><Text style={s.emptyIcon}>—</Text><Text style={s.emptyTitle}>{title}</Text><Text style={s.emptyCopy}>{copy}</Text></View>
}

export function Card({children,accent=false}:{children:React.ReactNode;accent?:boolean}){
  return <View style={[s.card,accent&&s.cardAccent]}>{children}</View>
}

export function BackHeader({title,subtitle,onBack}:{title:string;subtitle?:string;onBack:()=>void}){
  return <View style={s.backHeader}><Pressable onPress={onBack} style={s.backBtn}><Text style={s.backIcon}>‹</Text></Pressable><View style={{flex:1}}><Text style={s.backTitle}>{title}</Text>{subtitle?<Text style={s.backSub}>{subtitle}</Text>:null}</View></View>
}

const s=StyleSheet.create({
 sectionRow:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',marginBottom:10,marginTop:8},
 sectionTitle:{color:colors.white,fontSize:14,fontWeight:'600'},
 action:{color:colors.redBright,fontSize:11,fontWeight:'600'},
 pill:{paddingHorizontal:8,paddingVertical:4,borderRadius:5,alignSelf:'flex-start'},
 pillText:{fontSize:9,fontWeight:'600'},
 metric:{flex:1},metricValue:{color:colors.white,fontSize:18,fontWeight:'700'},metricLabel:{color:colors.subtle,fontSize:9,fontWeight:'500',marginTop:3},
 btn:{backgroundColor:colors.red,borderRadius:7,minHeight:40,paddingHorizontal:15,alignItems:'center',justifyContent:'center'},
 btnSecondary:{backgroundColor:colors.surface3},btnSmall:{minHeight:32,paddingHorizontal:11},btnText:{color:'#fff',fontSize:11,fontWeight:'600'},btnTextSecondary:{color:colors.white},
 search:{height:42,borderRadius:8,backgroundColor:colors.surface3,flexDirection:'row',alignItems:'center',paddingHorizontal:12,marginBottom:14},searchIcon:{color:colors.subtle,fontSize:18,marginRight:8},searchInput:{flex:1,color:colors.white,fontSize:13},
 empty:{alignItems:'center',paddingVertical:30,paddingHorizontal:28,backgroundColor:colors.surface,borderRadius:9},emptyIcon:{color:colors.subtle,fontSize:24},emptyTitle:{color:colors.white,fontWeight:'600',marginTop:8},emptyCopy:{color:colors.muted,fontSize:11,lineHeight:16,textAlign:'center',marginTop:5},
 card:{backgroundColor:colors.surface,borderRadius:9,padding:14,marginBottom:10},cardAccent:{backgroundColor:'#160C20',borderLeftWidth:3,borderLeftColor:colors.magenta},
 backHeader:{height:58,flexDirection:'row',alignItems:'center',gap:10,borderBottomWidth:1,borderBottomColor:colors.border,paddingHorizontal:14,backgroundColor:colors.surface},backBtn:{width:34,height:34,borderRadius:8,alignItems:'center',justifyContent:'center',backgroundColor:colors.surface3},backIcon:{color:colors.white,fontSize:26,lineHeight:28},backTitle:{color:colors.white,fontSize:15,fontWeight:'700'},backSub:{color:colors.subtle,fontSize:10,fontWeight:'500',marginTop:1},
});
