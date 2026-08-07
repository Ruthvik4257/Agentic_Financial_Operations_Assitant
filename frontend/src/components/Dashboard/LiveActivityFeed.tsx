import React from 'react';
import { Activity, Zap, ShieldCheck, AlertTriangle, ArrowRight } from 'lucide-react';
import { WebSocketEvent } from '../../types';

interface LiveActivityFeedProps {
  events: WebSocketEvent[];
  onSelectDispute: (disputeId: string) => void;
}

export const LiveActivityFeed: React.FC<LiveActivityFeedProps> = ({ events, onSelectDispute }) => {
  return (
    <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-blue-400 animate-pulse" />
          <h3 className="text-sm font-bold text-white tracking-wide uppercase">Real-Time Autonomous Agent Stream</h3>
        </div>
        <span className="text-xs text-gray-400 font-mono">WebSocket: 50ms broadcast</span>
      </div>

      <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
        {events.length === 0 ? (
          <div className="py-12 text-center text-gray-500 text-xs">
            Awaiting incoming customer dispute events from Telegram or Webhook...
          </div>
        ) : (
          events.map((evt, idx) => {
            const isAuto = evt.type.includes('AUTO_EXECUTED');
            const isHitl = evt.type.includes('HITL') || evt.type.includes('ESCALATION');
            
            return (
              <div
                key={idx}
                className="p-3 rounded-xl bg-gray-900/80 border border-gray-800/80 hover:border-gray-700 transition flex items-center justify-between text-xs group"
              >
                <div className="flex items-center space-x-3">
                  <div className={`p-1.5 rounded-lg ${isAuto ? 'bg-emerald-500/10 text-emerald-400' : isHitl ? 'bg-amber-500/10 text-amber-400' : 'bg-blue-500/10 text-blue-400'}`}>
                    {isAuto ? <Zap className="w-3.5 h-3.5" /> : isHitl ? <AlertTriangle className="w-3.5 h-3.5" /> : <ShieldCheck className="w-3.5 h-3.5" />}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-200">
                      {evt.type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-gray-400 text-[11px] font-mono mt-0.5">
                      {evt.dispute_id && <span className="mr-2 text-blue-400">{evt.dispute_id}</span>}
                      {evt.amount && <span className="mr-2 font-bold text-emerald-400">${evt.amount.toFixed(2)}</span>}
                      {evt.payment_entry && <span className="text-gray-500 font-mono">ERPNext: {evt.payment_entry}</span>}
                    </div>
                  </div>
                </div>

                {evt.dispute_id && (
                  <button
                    onClick={() => onSelectDispute(evt.dispute_id!)}
                    className="opacity-0 group-hover:opacity-100 transition px-2.5 py-1 rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 flex items-center space-x-1"
                  >
                    <span>Dossier</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
