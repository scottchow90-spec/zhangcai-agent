import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata={title:'掌财智能体 · 股票研究工作台',description:'以行情为起点，按53项股票技能组织的掌财智能体研究工作台。',icons:{icon:'/favicon.png',shortcut:'/favicon.png',apple:'/favicon.png'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="zh-CN"><body>{children}</body></html>}

