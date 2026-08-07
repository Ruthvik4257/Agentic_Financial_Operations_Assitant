import React, { useState } from 'react';
import { Send, CheckCircle2, AlertTriangle, ShieldCheck, Loader2, Sparkles } from 'lucide-react';
import { api } from '../../services/api';

export const CustomerDisputePortal: React.FC = () => {
  const [invoiceId, setInvoiceId] = useState('INV-2026-001');
  const [amount, setAmount] = useState<number>(150.0);
  const [reason, setReason] = useState('Hi, I was billed twice for my cloud subscription invoice.');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    try {
      const res = await api.simulateDispute(invoiceId, amount, reason);
      setResult(res);
    } catch (err) {
      console.error('Submission failed', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl glass-panel border border-gray-800">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-white tracking-tight">Customer Dispute & Resolution Intake Portal</h2>
        </div>
        <p className="text-xs text-gray-400 mt-1">
          Web self-service channel operating in parallel with the Telegram FinOps assistant.
        </p>
      </div>

      {/* Form and Live Response */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Input Form */}
        <form onSubmit={handleSubmit} className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-4">
          <div className="text-sm font-bold text-white tracking-wide">Submit a Billing Claim</div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-gray-400">ERPNext Invoice ID</label>
            <input
              type="text"
              value={invoiceId}
              onChange={(e) => setInvoiceId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
              placeholder="INV-2026-001"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-gray-400">Disputed Amount ($ USD)</label>
            <input
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value))}
              className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-gray-400">Dispute Reason / Claim Details</label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-xs text-white focus:outline-none focus:border-blue-500"
              placeholder="Describe why this charge is incorrect..."
              required
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/20"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Multi-Agent Investigation...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Submit to Autonomous AI Agent</span>
              </>
            )}
          </button>
        </form>

        {/* Right: Instant Autonomous Outcome */}
        <div className="p-6 rounded-2xl glass-panel border border-gray-800 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="text-sm font-bold text-white tracking-wide">Live Autonomous AI Resolution</div>

            {result ? (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-xl bg-gray-900/90 border border-gray-800 space-y-1">
                  <div className="text-gray-500 text-[10px]">DISPUTE ID</div>
                  <div className="text-blue-400 font-bold">{result.id}</div>
                </div>

                <div className="p-3 rounded-xl bg-gray-900/90 border border-gray-800 space-y-1">
                  <div className="text-gray-500 text-[10px]">STATUS & VERDICT</div>
                  <div className="flex items-center space-x-2">
                    {result.status === 'EXECUTED' && (
                      <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                        REFUND AUTO-EXECUTED
                      </span>
                    )}
                    {result.status === 'AWAITING_APPROVAL' && (
                      <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">
                        ESCALATED TO MANAGER (HITL)
                      </span>
                    )}
                  </div>
                </div>

                {result.erp_payment_entry_id && (
                  <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300">
                    <div className="text-[10px] text-emerald-400">ERPNEXT PAYMENT ENTRY</div>
                    <div className="font-bold">{result.erp_payment_entry_id}</div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-16 text-center text-gray-500 text-xs">
                Submit a claim on the left to watch the multi-agent pipeline investigate the invoice in real-time.
              </div>
            )}
          </div>

          <div className="p-3 rounded-xl bg-blue-950/20 border border-blue-500/20 text-[11px] text-blue-300 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-blue-400 flex-shrink-0" />
            <span>Cross-referenced against ERPNext Debtors ledger with cryptographic audit logging.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
