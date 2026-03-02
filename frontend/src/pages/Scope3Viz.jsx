import { useState } from 'react';
import NetworkGraph from '../components/NetworkGraph';
import AIExplanationPanel from '../components/AIExplanationPanel';

const MOCK_AI = `Scope 3 Supply Chain Analysis — Gemini Reasoning:

Tier-1 Suppliers: 4 direct suppliers identified. Steel Corp and Plastics Inc contribute ~68% of your upstream Scope 3 emissions.

High-Risk Nodes:
• Steel Corp: High carbon intensity (2.1 tCO₂ per $1000 revenue). No verified carbon reduction plan.
• Plastics Inc: Flagged for incomplete disclosure. Likely under-reporting.

Downstream Emissions: Logistics & end-of-life product emissions are not yet accounted for. Estimated additional 15% of total Scope 3.

Recommendation: Engage Steel Corp and Plastics Inc for joint emission reduction programs immediately.`;

export default function Scope3Viz() {
    const [loading, setLoading] = useState(false);
    const [aiText, setAiText] = useState('');
    const [fileUploaded, setFileUploaded] = useState(false);

    const handleAnalyze = async () => {
        setLoading(true); setAiText('');
        await new Promise((r) => setTimeout(r, 1500));
        setAiText(MOCK_AI);
        setLoading(false);
    };

    return (
        <div>
            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Scope 3 Visualization</h1>
                    <p className="page-sub">Supply chain network graph with AI-powered risk reasoning</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                        📁 Upload Manifest
                        <input type="file" accept=".csv,.xlsx,.pdf" style={{ display: 'none' }}
                            onChange={() => setFileUploaded(true)} />
                    </label>
                    <button id="scope3-analyze" className="btn btn-primary" onClick={handleAnalyze} disabled={loading}>
                        {loading ? '⏳ Analyzing...' : '🔍 Analyze with Gemini'}
                    </button>
                </div>
            </div>

            {/* Legend strip */}
            <div className="card card-sm mb-24 flex gap-20 items-center" style={{ flexWrap: 'wrap' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 600 }}>Supplier Risk:</span>
                {[['high', '#ff4d6d'], ['medium', '#ffd166'], ['low', '#00f5a0']].map(([r, c]) => (
                    <div key={r} style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '13px' }}>
                        <div style={{ width: '20px', height: '3px', background: c, borderRadius: '2px' }} />
                        <span style={{ color: 'var(--text-2)', textTransform: 'capitalize' }}>{r} Risk</span>
                    </div>
                ))}
                <div style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--text-muted)' }}>
                    {fileUploaded ? '✅ Manifest loaded' : 'Upload supplier manifest for real data'}
                </div>
            </div>

            {/* Graph */}
            <div className="card mb-24">
                <div className="card-title mb-16">Supply Chain Network</div>
                <NetworkGraph />
            </div>

            {/* Stats row */}
            <div className="stats-grid mb-24">
                {[
                    { icon: '🔗', value: '4', label: 'Tier-1 Suppliers' },
                    { icon: '🏭', value: '2', label: 'Tier-2 Suppliers' },
                    { icon: '⛔', value: '2', label: 'High-Risk Nodes' },
                    { icon: '📦', value: '68%', label: 'Emission Share (Top 2)' },
                ].map((s) => (
                    <div className="stat-card" key={s.label}>
                        <span className="stat-icon">{s.icon}</span>
                        <span className="stat-value">{s.value}</span>
                        <span className="stat-label">{s.label}</span>
                    </div>
                ))}
            </div>

            {/* AI Panel */}
            <AIExplanationPanel text={aiText} isLoading={loading} title="Gemini Scope 3 Reasoning" />
        </div>
    );
}
