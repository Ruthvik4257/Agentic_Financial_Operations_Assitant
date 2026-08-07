import React from 'react';
import { LayoutDashboard, ReceiptText, ShieldAlert, Database, History, Sliders } from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  pendingCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, pendingCount }) => {
  const navItems = [
    { id: 'overview', label: 'Operations Hub', icon: LayoutDashboard },
    { id: 'disputes', label: 'Dispute Queue', icon: ReceiptText, badge: pendingCount > 0 ? pendingCount : null },
    { id: 'policies', label: 'Policy Engine', icon: Sliders },
    { id: 'erp', label: 'ERPNext Mirror', icon: Database },
    { id: 'audit', label: 'Cryptographic Audit', icon: History },
  ];

  return (
    <aside className="w-64 border-r border-gray-800 bg-[#0B0F19] flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2">
          Management Controls
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-gray-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Telegram Assistant Box */}
      <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-2">
        <div className="flex items-center space-x-2 text-xs font-semibold text-blue-400">
          <ShieldAlert className="w-4 h-4" />
          <span>Telegram HITL Bot</span>
        </div>
        <p className="text-[11px] text-gray-400 leading-relaxed">
          Customer messages and manager 1-click approvals are routed in real-time.
        </p>
        <div className="text-[10px] text-gray-500 font-mono">
          Gateway: @BotFather Polling
        </div>
      </div>
    </aside>
  );
};
