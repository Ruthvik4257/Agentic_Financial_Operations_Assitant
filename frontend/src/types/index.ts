export interface Dispute {
  id: string;
  customer_id: string;
  invoice_id: string;
  amount: number;
  currency: string;
  reason: string;
  status: 'PENDING_INVESTIGATION' | 'AWAITING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'EXECUTED' | 'FAILED';
  fraud_score: number;
  risk_tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  is_duplicate_payment: boolean;
  forensic_summary?: string;
  gemini_reasoning?: string;
  erp_payment_entry_id?: string;
  erp_refund_status?: string;
  created_at?: string;
  updated_at?: string;
  resolved_at?: string;
}

export interface AuditLog {
  id: string;
  dispute_id: string;
  timestamp: string;
  action: string;
  agent_node: string;
  state_diff?: Record<string, any>;
  justification: string;
  previous_hash: string;
  current_hash: string;
}

export interface ERPInvoice {
  name: string;
  customer: string;
  customer_name?: string;
  posting_date: string;
  grand_total: number;
  outstanding_amount: number;
  status: string;
  currency: string;
  items?: Array<{
    item_code: string;
    item_name: string;
    qty: number;
    rate: number;
    amount: number;
  }>;
}

export interface ERPPayment {
  name: string;
  payment_type: string;
  party_type: string;
  party: string;
  paid_amount: number;
  received_amount: number;
  reference_no?: string;
  status: string;
  posting_date: string;
  remarks?: string;
}

export interface SystemMetrics {
  total_disputes: number;
  auto_resolved_count: number;
  auto_resolved_pct: number;
  refund_volume_usd: number;
  fraud_prevented_usd: number;
  pending_hitl_count: number;
  avg_resolution_seconds: number;
  erpnext_connected: boolean;
  langgraph_status: string;
}

export interface WebSocketEvent {
  type: string;
  dispute_id?: string;
  invoice_id?: string;
  amount?: number;
  payment_entry?: string;
  risk_score?: number;
  channel?: string;
  message?: string;
}
