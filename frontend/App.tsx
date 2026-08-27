import React,{useState} from 'react';
import { SafeAreaView,View,StatusBar,StyleSheet } from 'react-native';
import { colors } from './src/theme/colors';
import { MainTab,DetailRoute } from './src/types/navigation';
import { TopBar } from './src/components/TopBar';
import { BottomNav } from './src/components/BottomNav';
import { HomeScreen } from './src/screens/HomeScreen';
import { CompeteScreen } from './src/screens/CompeteScreen';
import { HubScreen } from './src/screens/HubScreen';
import { CareerScreen } from './src/screens/CareerScreen';
import { MoreScreen } from './src/screens/MoreScreen';
import { DetailScreen } from './src/screens/DetailScreens';

export default function App(){const[tab,setTab]=useState<MainTab>('HOME');const[detail,setDetail]=useState<DetailRoute|null>(null);const open=(r:DetailRoute)=>setDetail(r);const screen={HOME:<HomeScreen open={open}/>,COMPETE:<CompeteScreen open={open}/>,HUB:<HubScreen open={open}/>,CAREER:<CareerScreen open={open}/>,MORE:<MoreScreen open={open}/>} as Record<MainTab,React.ReactNode>;
return <SafeAreaView style={s.safe}><StatusBar barStyle="light-content" backgroundColor="#08080A"/>{detail?<DetailScreen route={detail} onBack={()=>setDetail(null)} open={open}/>:<><TopBar onNotifications={()=>open('NOTIFICATIONS')}/><View style={s.body}>{screen[tab]}</View><BottomNav active={tab} onChange={setTab}/></>}</SafeAreaView>}
const s=StyleSheet.create({safe:{flex:1,backgroundColor:colors.bg},body:{flex:1,backgroundColor:colors.bg}});
