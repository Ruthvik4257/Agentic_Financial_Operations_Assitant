import React from 'react';
import { ShieldCheck, Activity, Database, Bot, Bell } from 'lucide-react';
import { SystemMetrics } from '../../types';

interface NavbarProps {
  metrics: SystemMetrics | null;
  wsConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ metrics, wsConnected }) => {
  return (
    <header className="h-16 border-b border-gray-800 bg-[#0B0F19]/90 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
      {/* Brand Title */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg text-white tracking-tight">FinOps Agent</span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Enterprise v1.0
            </span>
          </div>
          <p className="text-xs text-gray-400">Autonomous Financial Operations & ERPNext Reconciliation</p>
        </div>
      </div>

      {/* Live System Badges */}
      <div className="flex items-center space-x-4">
        {/* ERPNext Live Indicator */}
        <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-gray-900 border border-gray-800 text-xs">
          <Database className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-gray-300 font-medium">ERPNext:</span>
          <span className="text-emerald-400 font-semibold">CONNECTED</span>
        </div>

        {/* LangGraph Active Indicator */}
        <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-gray-900 border border-gray-800 text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-gray-300 font-medium">LangGraph:</span>
          <span className="text-blue-400 font-semibold">ACTIVE</span>
        </div>

        {/* WebSocket Real-time Pulse */}
        <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-gray-900 border border-gray-800 text-xs">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-gray-400">{wsConnected ? 'Live Stream' : 'Disconnected'}</span>
        </div>
      </div>
    </header>
  );
};
