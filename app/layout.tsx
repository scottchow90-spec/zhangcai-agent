import type { Metadata } from 'next';
import './globals.css';
import DesktopRuntimeShell from './desktop-runtime-shell';
export const metadata: Metadata={title:'掌财桌面端',description:'14 个股票研究技能的本地运行、数据落盘与降级控制。',icons:{icon:'/favicon.png',shortcut:'/favicon.png',apple:'/favicon.png'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="zh-CN"><body><DesktopRuntimeShell />{children}</body></html>}

