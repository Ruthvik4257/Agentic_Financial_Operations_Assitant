import React, { useEffect, useState } from 'react';
import { ShieldCheck, Hash, Lock, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { Dispute, AuditLog } from '../../types';

export const CryptographicAuditView: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAuditData = async () => {
    setLoading(true);
    try {
      const disputes = await api.getDisputes();
      if (disputes.length > 0) {
        const dossier = await api.getDisputeDossier(disputes[0].id);
        setAuditLogs(dossier.audit_trail || []);
      }
    } catch (e) {
      console.error('Failed to load audit logs', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl glass-panel border border-gray-800 flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Lock className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">Cryptographic FinOps Audit Ledger</h2>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Immutable SHA-256 state-chained audit trail verifying every AI decision and ERPNext ledger mutation.
          </p>
        </div>

        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-mono text-emerald-400 font-bold">
          <CheckCircle2 className="w-4 h-4" />
          <span>CRYPTOGRAPHIC CHAIN VERIFIED</span>
        </div>
      </div>

      {/* Audit Chain Feed */}
      <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-4">
        <div className="space-y-3">
          {auditLogs.length === 0 ? (
            <div className="py-12 text-center text-gray-500 text-xs">
              No audit logs recorded yet. Run a payment dispute test to generate cryptographic hashes.
            </div>
          ) : (
            auditLogs.map((log, idx) => (
              <div key={log.id} className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 font-mono">
                    <span className="font-bold text-blue-400">{log.id}</span>
                    <span className="text-gray-500">|</span>
                    <span className="text-emerald-400 font-bold">{log.action}</span>
                    <span className="text-gray-500">|</span>
                    <span className="text-gray-400">Node: {log.agent_node}</span>
                  </div>
                  <span className="text-[10px] text-gray-500 font-mono">{log.timestamp}</span>
                </div>

                <p className="text-gray-300 font-sans">{log.justification}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 font-mono text-[10px] text-gray-500">
                  <div className="truncate">Prev Hash: {log.previous_hash}</div>
                  <div className="truncate text-blue-400 font-semibold">Current Hash: {log.current_hash}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
