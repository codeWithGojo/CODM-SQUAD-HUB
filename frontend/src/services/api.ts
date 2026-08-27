export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api/v1';
export async function api(path:string, options:RequestInit={}){const r=await fetch(`${API_BASE_URL}${path}`,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});if(!r.ok)throw new Error(await r.text());return r.json();}
