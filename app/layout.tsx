import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata={title:'掌财智能体 · 14技能网页运行台',description:'14 个电脑版技能的本地网页适配、数据落盘与降级控制。',icons:{icon:'/favicon.png',shortcut:'/favicon.png',apple:'/favicon.png'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="zh-CN"><body>{children}</body></html>}

