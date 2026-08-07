import React from 'react';
import { DollarSign, ShieldAlert, Zap, Clock } from 'lucide-react';
import { SystemMetrics } from '../../types';

interface KPICardsProps {
  metrics: SystemMetrics | null;
}

export const KPICards: React.FC<KPICardsProps> = ({ metrics }) => {
  const cards = [
    {
      title: 'Total Disputes Ingested',
      value: metrics ? metrics.total_disputes : '--',
      subtitle: 'From Telegram & Webhook',
      icon: ShieldAlert,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
    },
    {
      title: 'Autonomous Resolution',
      value: metrics ? `${metrics.auto_resolved_pct}%` : '--',
      subtitle: `${metrics ? metrics.auto_resolved_count : 0} refunded in < 2.0s`,
      icon: Zap,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      title: 'Refund Volume Executed',
      value: metrics ? `$${metrics.refund_volume_usd.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '$0.00',
      subtitle: 'Posted to ERPNext Ledger 2110',
      icon: DollarSign,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20',
    },
    {
      title: 'Mean Resolution Speed',
      value: metrics ? `${metrics.avg_resolution_seconds}s` : '1.4s',
      subtitle: 'From message to ledger entry',
      icon: Clock,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-5 rounded-2xl border ${card.bg} glass-panel flex flex-col justify-between transition-all duration-200 hover:scale-[1.01]`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{card.title}</span>
              <div className={`p-2 rounded-xl bg-gray-900/60 border border-gray-800 ${card.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4">
              <div className="text-2xl font-extrabold text-white tracking-tight">{card.value}</div>
              <div className="text-xs text-gray-400 mt-1">{card.subtitle}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
