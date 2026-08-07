import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Common/Navbar';
import { Sidebar } from './components/Common/Sidebar';
import { KPICards } from './components/Dashboard/KPICards';
import { LiveActivityFeed } from './components/Dashboard/LiveActivityFeed';
import { DisputeTable } from './components/DisputeQueue/DisputeTable';
import { InvestigationDossierModal } from './components/Dossier/InvestigationDossierModal';
import { ERPNextLedgerView } from './components/ERPNextMirror/ERPNextLedgerView';
import { CryptographicAuditView } from './components/AuditLedger/CryptographicAuditView';
import { PolicyManagerView } from './components/PolicyEngine/PolicyManagerView';
import { CustomerDisputePortal } from './components/CustomerPortal/CustomerDisputePortal';
import { api } from './services/api';
import { useWebSocket } from './hooks/useWebSocket';
import { Dispute, SystemMetrics, WebSocketEvent } from './types';
import { Sparkles, Zap, ShieldAlert } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedDossier, setSelectedDossier] = useState<any | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [m, d] = await Promise.all([api.getMetrics(), api.getDisputes()]);
      setMetrics(m);
      setDisputes(d);
    } catch (e) {
      console.error('Failed to load initial data', e);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleWebSocketEvent = useCallback((event: WebSocketEvent) => {
    loadData();
  }, [loadData]);

  const { isConnected, events } = useWebSocket(handleWebSocketEvent);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenDossier = async (disputeId: string) => {
    try {
      const data = await api.getDisputeDossier(disputeId);
      setSelectedDossier(data);
    } catch (e) {
      console.error('Failed to load dossier', e);
    }
  };

  const handleQuickApprove = async (disputeId: string) => {
    await api.approveDispute(disputeId, 'Approved from Operations Hub 1-Click');
    loadData();
  };

  const handleQuickReject = async (disputeId: string) => {
    await api.rejectDispute(disputeId, 'Rejected from Operations Hub 1-Click');
    loadData();
  };

  const handleTriggerSimulation = async (scenario: 'double_charge' | 'high_value' | 'fraud') => {
    setSimulating(true);
    try {
      if (scenario === 'double_charge') {
        await api.simulateDispute('INV-2026-001', 150.00, 'Customer charged twice for seat license');
      } else if (scenario === 'high_value') {
        await api.simulateDispute('INV-2026-045', 850.00, 'Customer disputing dedicated enterprise support surcharge');
      } else {
        await api.simulateDispute('INV-2026-102', 2500.00, 'High anomaly overseas chargeback claim');
      }
      await loadData();
    } catch (e) {
      console.error('Simulation failed', e);
    } finally {
      setSimulating(false);
    }
  };

  const pendingCount = disputes.filter((d) => d.status === 'AWAITING_APPROVAL').length;

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <Navbar metrics={metrics} wsConnected={isConnected} />

      {/* Main Layout */}
      <div className="flex flex-1">
        {/* Left Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          pendingCount={pendingCount}
        />

        {/* Dynamic Content Body */}
        <main className="flex-1 p-8 overflow-y-auto max-w-7xl mx-auto space-y-6 w-full">
          {/* Quick Simulation Toolbar for Live Demos & Judges */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-purple-900/30 border border-blue-500/20 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Sparkles className="w-4 h-4 animate-spin" />
              </div>
              <div>
                <div className="text-xs font-bold text-white tracking-wide uppercase">Interactive Demo Simulation Deck</div>
                <div className="text-[11px] text-gray-400">Trigger live financial scenarios to test LangGraph, Gemini & ERPNext</div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleTriggerSimulation('double_charge')}
                disabled={simulating}
                className="px-3 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition flex items-center space-x-1.5"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Simulate $150 (Auto-Approve)</span>
              </button>
              <button
                onClick={() => handleTriggerSimulation('high_value')}
                disabled={simulating}
                className="px-3 py-1.5 rounded-xl bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 text-xs font-bold transition flex items-center space-x-1.5"
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Simulate $850 (HITL Gate)</span>
              </button>
            </div>
          </div>

          {currentTab === 'overview' && (
            <div className="space-y-6">
              {/* FinOps KPI Cards */}
              <KPICards metrics={metrics} />

              {/* 2-Column Main Workspace */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <DisputeTable
                    disputes={disputes}
                    onSelectDispute={handleOpenDossier}
                    onQuickApprove={handleQuickApprove}
                    onQuickReject={handleQuickReject}
                    onRefresh={loadData}
                    loading={loading}
                  />
                </div>
                <div className="lg:col-span-1">
                  <LiveActivityFeed
                    events={events}
                    onSelectDispute={handleOpenDossier}
                  />
                </div>
              </div>
            </div>
          )}

          {currentTab === 'disputes' && (
            <DisputeTable
              disputes={disputes}
              onSelectDispute={handleOpenDossier}
              onQuickApprove={handleQuickApprove}
              onQuickReject={handleQuickReject}
              onRefresh={loadData}
              loading={loading}
            />
          )}

          {currentTab === 'portal' && <CustomerDisputePortal />}

          {currentTab === 'policies' && <PolicyManagerView />}

          {currentTab === 'erp' && <ERPNextLedgerView />}

          {currentTab === 'audit' && <CryptographicAuditView />}
        </main>
      </div>

      {/* Investigation Dossier Modal */}
      {selectedDossier && (
        <InvestigationDossierModal
          dossier={selectedDossier}
          onClose={() => setSelectedDossier(null)}
          onApprove={handleQuickApprove}
          onReject={handleQuickReject}
        />
      )}
    </div>
  );
};
