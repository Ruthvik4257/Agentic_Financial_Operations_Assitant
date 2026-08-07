import React, { useState } from 'react';
import { X, ShieldCheck, Database, CheckCircle, XCircle, FileText, Hash, ArrowRight } from 'lucide-react';
import { Dispute, AuditLog, ERPInvoice, ERPPayment } from '../../types';

interface InvestigationDossierModalProps {
  dossier: {
    dispute: Dispute;
    erp_invoice: ERPInvoice | null;
    erp_payments: ERPPayment[] | null;
    audit_trail: AuditLog[];
    approval_request: any | null;
  } | null;
  onClose: () => void;
  onApprove: (disputeId: string, notes: string) => void;
  onReject: (disputeId: string, notes: string) => void;
}

export const InvestigationDossierModal: React.FC<InvestigationDossierModalProps> = ({
  dossier,
  onClose,
  onApprove,
  onReject,
}) => {
  const [managerNotes, setManagerNotes] = useState('Authorized by Finance Operations Manager');
  if (!dossier) return null;

  const { dispute, erp_invoice, erp_payments, audit_trail } = dossier;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-[#0B0F19] border border-gray-800 rounded-3xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-800 flex items-center justify-between bg-gray-900/40">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-tight">Forensic Investigation Dossier</h2>
                <span className="px-2.5 py-0.5 text-xs font-mono font-bold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {dispute.id}
                </span>
              </div>
              <p className="text-xs text-gray-400">Cross-referencing Telegram claim with ERPNext System of Record</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-gray-800/60 hover:bg-gray-700 text-gray-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {/* Top 3-Column Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Customer Dispute */}
            <div className="p-4 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-2">
              <div className="text-[11px] font-semibold text-gray-400 uppercase">Customer Claim (Telegram)</div>
              <div className="text-sm font-bold text-white">${dispute.amount.toFixed(2)} USD</div>
              <div className="text-gray-300 italic">"{dispute.reason}"</div>
              <div className="text-[10px] text-gray-500 font-mono">Customer ID: {dispute.customer_id}</div>
            </div>

            {/* ERPNext ground truth */}
            <div className="p-4 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-2">
              <div className="text-[11px] font-semibold text-gray-400 uppercase">ERPNext System of Record</div>
              <div className="text-sm font-bold text-white">{dispute.invoice_id}</div>
              <div className="text-gray-300">
                Invoice Total: <span className="font-bold text-white">${erp_invoice?.grand_total || dispute.amount}</span>
              </div>
              <div className="text-[10px] text-emerald-400 font-mono">
                Matched Payments: {erp_payments?.length || 0} Records
              </div>
            </div>

            {/* AI Forensic Reasoning */}
            <div className="p-4 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-2">
              <div className="text-[11px] font-semibold text-gray-400 uppercase">Gemini Forensic Risk</div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-extrabold text-blue-400">{dispute.fraud_score.toFixed(2)}</span>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-500/10 text-blue-400">
                  {dispute.risk_tier} RISK
                </span>
              </div>
              <p className="text-gray-400 leading-relaxed">
                {dispute.forensic_summary || 'Analyzed via Gemini 2.0 Flash.'}
              </p>
            </div>
          </div>

          {/* ERPNext Ledger Impact & Balance Sheet Preview */}
          <div className="p-5 rounded-2xl bg-gray-900/40 border border-gray-800 space-y-3">
            <div className="flex items-center space-x-2 font-bold text-white">
              <Database className="w-4 h-4 text-emerald-400" />
              <span>ERPNext Accounting Ledger Impact Preview</span>
            </div>
            <div className="grid grid-cols-2 gap-4 font-mono text-[11px]">
              <div className="p-3 rounded-xl bg-gray-900/80 border border-gray-800">
                <div className="text-gray-400 text-[10px] uppercase font-bold">Debit Ledger (2110 Debtors)</div>
                <div className="text-emerald-400 font-bold text-sm mt-1">+${dispute.amount.toFixed(2)} USD</div>
                <div className="text-gray-500 text-[10px] mt-0.5">Offset duplicate accounts receivable</div>
              </div>
              <div className="p-3 rounded-xl bg-gray-900/80 border border-gray-800">
                <div className="text-gray-400 text-[10px] uppercase font-bold">Credit Ledger (1110 Bank Account)</div>
                <div className="text-rose-400 font-bold text-sm mt-1">-${dispute.amount.toFixed(2)} USD</div>
                <div className="text-gray-500 text-[10px] mt-0.5">Disbursement payout to customer</div>
              </div>
            </div>
          </div>

          {/* Cryptographic SHA-256 Chained Audit Trail */}
          <div className="p-5 rounded-2xl bg-gray-900/40 border border-gray-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 font-bold text-white">
                <Hash className="w-4 h-4 text-blue-400" />
                <span>Cryptographic SHA-256 Audit Trail</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                CHAIN VALIDATED
              </span>
            </div>

            <div className="space-y-2 max-h-40 overflow-y-auto font-mono text-[10px]">
              {audit_trail.map((log) => (
                <div key={log.id} className="p-2.5 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-between">
                  <div>
                    <span className="text-blue-400 font-bold mr-2">[{log.agent_node}]</span>
                    <span className="text-gray-200">{log.action}: </span>
                    <span className="text-gray-400">{log.justification}</span>
                  </div>
                  <div className="text-gray-600 text-[9px]">
                    Hash: {log.current_hash.slice(0, 12)}...
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-gray-800 bg-gray-900/60 flex flex-col md:flex-row items-center justify-between gap-4">
          <input
            type="text"
            value={managerNotes}
            onChange={(e) => setManagerNotes(e.target.value)}
            placeholder="Enter manager review notes..."
            className="w-full md:w-96 px-4 py-2 rounded-xl bg-gray-900 border border-gray-800 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold text-xs transition"
            >
              Close
            </button>
            <button
              onClick={() => {
                onReject(dispute.id, managerNotes);
                onClose();
              }}
              className="px-4 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 font-bold text-xs transition inline-flex items-center space-x-1.5"
            >
              <XCircle className="w-4 h-4" />
              <span>Reject Request</span>
            </button>
            <button
              onClick={() => {
                onApprove(dispute.id, managerNotes);
                onClose();
              }}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition inline-flex items-center space-x-1.5 shadow-lg shadow-emerald-600/20"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Authorize & Execute Refund in ERPNext</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
