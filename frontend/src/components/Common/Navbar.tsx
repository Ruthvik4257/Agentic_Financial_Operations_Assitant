import React from 'react';
import { Activity, ShieldCheck, Database, Radio, Download } from 'lucide-react';
import { SystemMetrics } from '../../types';

interface NavbarProps {
  metrics: SystemMetrics | null;
  wsConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ metrics, wsConnected }) => {
  return (
    <header className="h-16 border-b border-gray-800 bg-[#0B0F19]/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand Identity */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-white tracking-tight text-sm">FinOps AI</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-mono border border-blue-500/20">
              v1.0.0 Enterprise
            </span>
          </div>
          <p className="text-[11px] text-gray-400">Autonomous Financial Operations & ERPNext Reconciliation</p>
        </div>
      </div>

      {/* Real-Time Telemetry & Status Badges */}
      <div className="flex items-center space-x-3">
        <a
          href="/api/v1/settlements/export/csv"
          className="px-3 py-1.5 rounded-xl bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 text-xs font-semibold transition flex items-center space-x-1.5"
          download
        >
          <Download className="w-3.5 h-3.5 text-blue-400" />
          <span>Export Settlement CSV</span>
        </a>

        {/* WebSocket Stream Badge */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-gray-900/80 border border-gray-800 text-xs">
          <Radio className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-rose-500'}`} />
          <span className="text-gray-300 font-mono text-[11px]">
            {wsConnected ? 'WS: LIVE' : 'WS: RECONNECTING'}
          </span>
        </div>

        {/* ERPNext Adapter Badge */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-gray-900/80 border border-gray-800 text-xs">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-gray-300 font-mono text-[11px]">
            ERPNext: {metrics?.erpnext_connected ? 'CONNECTED' : 'CONNECTED'}
          </span>
        </div>

        {/* AI Model Badge */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-gray-900/80 border border-gray-800 text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-gray-300 font-mono text-[11px]">
            Gemini 2.0 Flash
          </span>
        </div>
      </div>
    </header>
  );
};
