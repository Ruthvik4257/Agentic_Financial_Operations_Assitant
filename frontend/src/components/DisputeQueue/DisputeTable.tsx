import React, { useState } from 'react';
import { Shield, CheckCircle, XCircle, Eye, AlertCircle, RefreshCw } from 'lucide-react';
import { Dispute } from '../../types';

interface DisputeTableProps {
  disputes: Dispute[];
  onSelectDispute: (disputeId: string) => void;
  onQuickApprove: (disputeId: string) => void;
  onQuickReject: (disputeId: string) => void;
  onRefresh: () => void;
  loading: boolean;
}

export const DisputeTable: React.FC<DisputeTableProps> = ({
  disputes,
  onSelectDispute,
  onQuickApprove,
  onQuickReject,
  onRefresh,
  loading,
}) => {
  const [filter, setFilter] = useState<string>('ALL');

  const filteredDisputes = disputes.filter((d) => {
    if (filter === 'ALL') return true;
    return d.status === filter;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'EXECUTED':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">EXECUTED (REFUNDED)</span>;
      case 'AWAITING_APPROVAL':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">AWAITING APPROVAL</span>;
      case 'REJECTED':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">REJECTED</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">INVESTIGATING</span>;
    }
  };

  const getRiskBadge = (score: number, tier: string) => {
    const color = score > 0.6 ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' : score > 0.3 ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    return (
      <div className={`inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-lg border text-xs font-mono font-bold ${color}`}>
        <Shield className="w-3 h-3" />
        <span>{score.toFixed(2)} ({tier})</span>
      </div>
    );
  };

  return (
    <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-4">
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Financial Operations Queue</h2>
          <p className="text-xs text-gray-400">Continuous AI investigation and ERPNext ledger reconciliation</p>
        </div>

        <div className="flex items-center space-x-2">
          {['ALL', 'AWAITING_APPROVAL', 'EXECUTED', 'REJECTED'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                filter === f
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-gray-900 text-gray-400 hover:text-white border border-gray-800'
              }`}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
          <button
            onClick={onRefresh}
            className="p-2 rounded-xl bg-gray-900 border border-gray-800 text-gray-400 hover:text-white transition"
            title="Refresh disputes"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Disputes Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-gray-900/60 text-gray-400 uppercase tracking-wider font-semibold border-b border-gray-800">
            <tr>
              <th className="py-3 px-4">Dispute ID</th>
              <th className="py-3 px-4">Customer</th>
              <th className="py-3 px-4">ERPNext Invoice</th>
              <th className="py-3 px-4">Amount ($)</th>
              <th className="py-3 px-4">Fraud Risk</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {filteredDisputes.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-gray-500">
                  No financial disputes matching filter. Send a test dispute via Telegram!
                </td>
              </tr>
            ) : (
              filteredDisputes.map((d) => (
                <tr key={d.id} className="hover:bg-gray-800/30 transition group">
                  <td className="py-3.5 px-4 font-mono font-bold text-blue-400">{d.id}</td>
                  <td className="py-3.5 px-4 font-semibold text-gray-200">{d.customer_id}</td>
                  <td className="py-3.5 px-4 font-mono text-gray-300">
                    <span className="px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-300">
                      {d.invoice_id}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-extrabold text-white">
                    ${d.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3.5 px-4">{getRiskBadge(d.fraud_score, d.risk_tier)}</td>
                  <td className="py-3.5 px-4">{getStatusBadge(d.status)}</td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    <button
                      onClick={() => onSelectDispute(d.id)}
                      className="px-2.5 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition font-medium inline-flex items-center space-x-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Dossier</span>
                    </button>

                    {d.status === 'AWAITING_APPROVAL' && (
                      <>
                        <button
                          onClick={() => onQuickApprove(d.id)}
                          className="px-2.5 py-1 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 font-bold transition inline-flex items-center space-x-1 border border-emerald-500/30"
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                        <button
                          onClick={() => onQuickReject(d.id)}
                          className="px-2.5 py-1 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 font-bold transition inline-flex items-center space-x-1 border border-rose-500/30"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
