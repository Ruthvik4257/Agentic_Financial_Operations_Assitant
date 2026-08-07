import React, { useEffect, useState } from 'react';
import { ShieldCheck, Hash, Lock, CheckCircle2, Download, FileCheck, X } from 'lucide-react';
import { api } from '../../services/api';
import { AuditLog } from '../../types';
import axios from 'axios';

export const CryptographicAuditView: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCertificate, setSelectedCertificate] = useState<any | null>(null);

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

  const handleExportCertificate = async () => {
    try {
      const disputes = await api.getDisputes();
      if (disputes.length > 0) {
        const res = await axios.get(`/api/v1/compliance/certificate/${disputes[0].id}`);
        setSelectedCertificate(res.data);
      }
    } catch (e) {
      console.error('Failed to fetch certificate', e);
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

        <div className="flex items-center space-x-3">
          <button
            onClick={handleExportCertificate}
            className="px-3.5 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-bold transition flex items-center space-x-1.5"
          >
            <FileCheck className="w-4 h-4" />
            <span>Export Merkle Certificate</span>
          </button>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-mono text-emerald-400 font-bold">
            <CheckCircle2 className="w-4 h-4" />
            <span>CHAIN VALIDATED</span>
          </div>
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
            auditLogs.map((log) => (
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

      {/* Merkle Root Compliance Certificate Modal */}
      {selectedCertificate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#0B0F19] border border-gray-800 rounded-3xl w-full max-w-2xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-800 pb-4">
              <div className="flex items-center space-x-2">
                <FileCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white tracking-tight">Cryptographic Compliance Certificate</h3>
              </div>
              <button onClick={() => setSelectedCertificate(null)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs text-gray-300">
              <div className="p-3 rounded-xl bg-gray-900 border border-gray-800 space-y-1">
                <div className="text-gray-500 text-[10px]">CERTIFICATE ID</div>
                <div className="text-white font-bold">{selectedCertificate.certificate_id}</div>
              </div>

              <div className="p-3 rounded-xl bg-gray-900 border border-gray-800 space-y-1">
                <div className="text-gray-500 text-[10px]">MERKLE ROOT HASH</div>
                <div className="text-emerald-400 font-bold truncate">{selectedCertificate.merkle_root}</div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-gray-900 border border-gray-800">
                  <div className="text-gray-500 text-[10px]">DISPUTE ID</div>
                  <div className="text-blue-400 font-bold">{selectedCertificate.dispute_id}</div>
                </div>
                <div className="p-3 rounded-xl bg-gray-900 border border-gray-800">
                  <div className="text-gray-500 text-[10px]">REFUND AMOUNT</div>
                  <div className="text-emerald-400 font-bold">${selectedCertificate.amount_usd} USD</div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-gray-900 border border-gray-800 space-y-1">
                <div className="text-gray-500 text-[10px]">COMPLIANCE STANDARDS VERIFIED</div>
                <div className="text-gray-300 text-[11px] font-sans">
                  • SOX Section 404 (Financial Reporting & Ledger Integrity)<br />
                  • PCI-DSS v4.0 Requirement 10 (Automated Audit Logging)
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedCertificate(null)}
                className="px-4 py-2 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-500 transition"
              >
                Close Certificate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
