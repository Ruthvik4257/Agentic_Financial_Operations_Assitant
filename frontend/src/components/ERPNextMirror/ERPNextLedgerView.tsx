import React, { useEffect, useState } from 'react';
import { Database, ArrowUpRight, RefreshCw, FileText, CheckCircle2 } from 'lucide-react';
import { ERPInvoice, ERPPayment } from '../../types';
import { api } from '../../services/api';

export const ERPNextLedgerView: React.FC = () => {
  const [invoices, setInvoices] = useState<ERPInvoice[]>([]);
  const [payments, setPayments] = useState<ERPPayment[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchERPData = async () => {
    setLoading(true);
    try {
      const [invData, payData] = await Promise.all([
        api.getERPInvoices(),
        api.getERPPayments(),
      ]);
      setInvoices(invData);
      setPayments(payData);
    } catch (e) {
      console.error('Failed to fetch ERP data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchERPData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl glass-panel border border-gray-800 flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">ERPNext System of Record Mirror</h2>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Real-time reflection of Frappe DocTypes (<span className="text-blue-400 font-mono">Sales Invoice</span>, <span className="text-emerald-400 font-mono">Payment Entry</span>).
          </p>
        </div>
        <button
          onClick={fetchERPData}
          className="px-3.5 py-2 rounded-xl bg-gray-900 border border-gray-800 text-xs font-semibold text-gray-300 hover:text-white flex items-center space-x-2 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          <span>Sync ERPNext</span>
        </button>
      </div>

      {/* Invoices & Payments Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Invoices */}
        <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 font-bold text-white text-sm">
              <FileText className="w-4 h-4 text-blue-400" />
              <span>DocType: Sales Invoice</span>
            </div>
            <span className="text-xs font-mono text-gray-500">{invoices.length} records</span>
          </div>

          <div className="space-y-2.5 max-h-[420px] overflow-y-auto">
            {invoices.map((inv) => (
              <div key={inv.name} className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-blue-400">{inv.name}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {inv.status}
                  </span>
                </div>
                <div className="flex items-center justify-between text-gray-300">
                  <span>Customer: {inv.customer_name || inv.customer}</span>
                  <span className="font-bold text-white">${inv.grand_total.toFixed(2)} USD</span>
                </div>
                <div className="text-[10px] text-gray-500 font-mono">
                  Posting Date: {inv.posting_date} | Outstanding: ${inv.outstanding_amount.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Payment Entries */}
        <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 font-bold text-white text-sm">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>DocType: Payment Entry (Settlements & Refunds)</span>
            </div>
            <span className="text-xs font-mono text-gray-500">{payments.length} records</span>
          </div>

          <div className="space-y-2.5 max-h-[420px] overflow-y-auto">
            {payments.map((p) => {
              const isRefund = p.payment_type === 'Pay';
              return (
                <div key={p.name} className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-emerald-400">{p.name}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${isRefund ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'}`}>
                      {isRefund ? 'REFUND (PAY)' : 'PAYMENT (RECEIVE)'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-gray-300">
                    <span>Party: {p.party}</span>
                    <span className={`font-bold ${isRefund ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {isRefund ? '-' : '+'}${p.paid_amount.toFixed(2)} USD
                    </span>
                  </div>
                  {p.remarks && (
                    <div className="text-[10px] text-gray-400 italic">
                      Remarks: {p.remarks}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
