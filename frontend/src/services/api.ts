import axios from 'axios';
import { Dispute, AuditLog, ERPInvoice, ERPPayment, SystemMetrics } from '../types';

const API_BASE = '/api/v1';

export const api = {
  getMetrics: async (): Promise<SystemMetrics> => {
    const res = await axios.get(`${API_BASE}/metrics`);
    return res.data;
  },

  getDisputes: async (status?: string, risk_tier?: string): Promise<Dispute[]> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (risk_tier) params.append('risk_tier', risk_tier);
    const res = await axios.get(`${API_BASE}/disputes`, { params });
    return res.data;
  },

  simulateDispute: async (invoiceId: string, amount: number, reason: string) => {
    const res = await axios.post(`${API_BASE}/disputes/simulate`, {
      customer_id: 'CUST-001',
      invoice_id: invoiceId,
      amount: amount,
      reason: reason,
      currency: 'USD',
    });
    return res.data;
  },

  getDisputeDossier: async (disputeId: string) => {
    const res = await axios.get(`${API_BASE}/disputes/${disputeId}`);
    return res.data;
  },

  approveDispute: async (disputeId: string, managerNotes: string = 'Approved from Executive Hub') => {
    const res = await axios.post(`${API_BASE}/approvals/${disputeId}`, {
      manager_id: 'MGR-EXECUTIVE',
      decision: 'APPROVED',
      manager_notes: managerNotes,
      channel: 'DASHBOARD',
    });
    return res.data;
  },

  rejectDispute: async (disputeId: string, managerNotes: string = 'Rejected by Executive Manager') => {
    const res = await axios.post(`${API_BASE}/approvals/${disputeId}`, {
      manager_id: 'MGR-EXECUTIVE',
      decision: 'REJECTED',
      manager_notes: managerNotes,
      channel: 'DASHBOARD',
    });
    return res.data;
  },

  getERPInvoices: async (): Promise<ERPInvoice[]> => {
    const res = await axios.get(`${API_BASE}/erp/invoices`);
    return res.data;
  },

  getERPPayments: async (): Promise<ERPPayment[]> => {
    const res = await axios.get(`${API_BASE}/erp/payments`);
    return res.data;
  },
};
