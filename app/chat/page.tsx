import ChatClient from './chat-client';
import type { Metadata } from 'next';

export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const metadata: Metadata = {
  title: '掌财研究工作台',
  description: '股票技能聊天工作台：确认后运行，研究报告本地归档。',
};

export default function ChatPage() {
  return <ChatClient />;
}
