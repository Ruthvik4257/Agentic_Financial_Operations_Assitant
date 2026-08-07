import React, { useEffect, useState } from 'react';
import { Sliders, ShieldCheck, CheckCircle2, Lock, AlertTriangle, Save } from 'lucide-react';
import axios from 'axios';

interface PolicyConfig {
  max_auto_refund_limit: number;
  max_fraud_risk_threshold: number;
  max_daily_refund_cap: number;
  require_2fa_above: number;
  auto_block_suspicious_accounts: boolean;
}

export const PolicyManagerView: React.FC = () => {
  const [policy, setPolicy] = useState<PolicyConfig>({
    max_auto_refund_limit: 200.0,
    max_fraud_risk_threshold: 0.30,
    max_daily_refund_cap: 5000.0,
    require_2fa_above: 1000.0,
    auto_block_suspicious_accounts: true,
  });
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    axios.get('/api/v1/policies').then((res) => {
      if (res.data) setPolicy(res.data);
    }).catch(console.error);
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await axios.put('/api/v1/policies', policy);
      setPolicy(res.data);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error('Failed to update policies', e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl glass-panel border border-gray-800 flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">Financial Governance Policy Customizer</h2>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Configure dynamic autonomous execution ceilings, fraud risk gates, and Human-in-the-Loop thresholds.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition flex items-center space-x-2 shadow-lg shadow-blue-500/20"
        >
          {saved ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Save className="w-4 h-4" />}
          <span>{saved ? 'Policies Committed' : saving ? 'Saving...' : 'Commit Policies'}</span>
        </button>
      </div>

      {/* Policy Controls Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
        {/* Control 1: Max Auto-Refund Limit */}
        <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-bold text-white text-sm">Autonomous Refund Limit ($)</div>
            <span className="px-3 py-1 rounded-xl bg-emerald-500/10 text-emerald-400 font-mono font-bold text-sm border border-emerald-500/20">
              ${policy.max_auto_refund_limit.toFixed(2)} USD
            </span>
          </div>
          <p className="text-gray-400 text-[11px]">
            Any refund below this amount executes in ERPNext automatically if fraud risk is safe. Higher amounts force Human-in-the-Loop approval.
          </p>
          <input
            type="range"
            min="50"
            max="1000"
            step="25"
            value={policy.max_auto_refund_limit}
            onChange={(e) => setPolicy({ ...policy, max_auto_refund_limit: parseFloat(e.target.value) })}
            className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        {/* Control 2: Max Fraud Risk Tolerance */}
        <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-bold text-white text-sm">AI Risk Tolerance Threshold</div>
            <span className="px-3 py-1 rounded-xl bg-blue-500/10 text-blue-400 font-mono font-bold text-sm border border-blue-500/20">
              {policy.max_fraud_risk_threshold.toFixed(2)}
            </span>
          </div>
          <p className="text-gray-400 text-[11px]">
            Calculated by Gemini 2.0 Flash. If risk exceeds this value, autonomous execution is blocked.
          </p>
          <input
            type="range"
            min="0.10"
            max="0.80"
            step="0.05"
            value={policy.max_fraud_risk_threshold}
            onChange={(e) => setPolicy({ ...policy, max_fraud_risk_threshold: parseFloat(e.target.value) })}
            className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        {/* Control 3: Daily Refund Outflow Cap */}
        <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-bold text-white text-sm">Daily Capital Outflow Cap ($)</div>
            <span className="px-3 py-1 rounded-xl bg-amber-500/10 text-amber-400 font-mono font-bold text-sm border border-amber-500/20">
              ${policy.max_daily_refund_cap.toLocaleString()} USD
            </span>
          </div>
          <p className="text-gray-400 text-[11px]">
            Circuit breaker: Total autonomous refunds across all customers will not exceed this limit per 24 hours.
          </p>
          <input
            type="range"
            min="1000"
            max="25000"
            step="1000"
            value={policy.max_daily_refund_cap}
            onChange={(e) => setPolicy({ ...policy, max_daily_refund_cap: parseFloat(e.target.value) })}
            className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        {/* Control 4: Mandatory 2FA Gate */}
        <div className="p-6 rounded-2xl glass-panel border border-gray-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-bold text-white text-sm">High-Value 2FA Gate ($)</div>
            <span className="px-3 py-1 rounded-xl bg-purple-500/10 text-purple-400 font-mono font-bold text-sm border border-purple-500/20">
              ${policy.require_2fa_above.toLocaleString()} USD
            </span>
          </div>
          <p className="text-gray-400 text-[11px]">
            Any transaction exceeding this limit requires dual manager sign-off on Telegram and Web Operations Hub.
          </p>
          <input
            type="range"
            min="500"
            max="5000"
            step="250"
            value={policy.require_2fa_above}
            onChange={(e) => setPolicy({ ...policy, require_2fa_above: parseFloat(e.target.value) })}
            className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>
      </div>
    </div>
  );
};
