import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Common/Navbar';
import { Sidebar } from './components/Common/Sidebar';
import { KPICards } from './components/Dashboard/KPICards';
import { LiveActivityFeed } from './components/Dashboard/LiveActivityFeed';
import { DisputeTable } from './components/DisputeQueue/DisputeTable';
import { InvestigationDossierModal } from './components/Dossier/InvestigationDossierModal';
import { ERPNextLedgerView } from './components/ERPNextMirror/ERPNextLedgerView';
import { CryptographicAuditView } from './components/AuditLedger/CryptographicAuditView';
import { api } from './services/api';
import { useWebSocket } from './hooks/useWebSocket';
import { Dispute, SystemMetrics, WebSocketEvent } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedDossier, setSelectedDossier] = useState<any | null>(null);

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
    // Refresh metrics & table on financial events
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
