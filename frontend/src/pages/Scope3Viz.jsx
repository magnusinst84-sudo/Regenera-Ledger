import { useState } from 'react';
import NetworkGraph from '../components/NetworkGraph';
import AIExplanationPanel from '../components/AIExplanationPanel';
import api, { analyzeScope3 } from '../api/api';


export default function Scope3Viz() {
    const [loading, setLoading] = useState(false);
    const [aiText, setAiText] = useState('');
    const [fileUploaded, setFileUploaded] = useState(false);
    const [graphData, setGraphData] = useState({ nodes: [], edges: [], summary: {} });

    // Files state
    const [esgFile, setEsgFile] = useState(null);
    const [supplierFile, setSupplierFile] = useState(null);

    const handleAnalyze = async () => {
        if (!esgFile || !supplierFile) {
            alert("Please upload both an ESG report and a supplier manifest.");
            return;
        }

        setLoading(true);
        setAiText('');

        try {
            const formData = new FormData();
            formData.append('esg_file', esgFile);
            formData.append('supplier_file', supplierFile);

            const response = await analyzeScope3(formData);

            const { result } = response.data;
            setAiText(result.forensic_explanation || "No forensic explanation returned.");
            if (result.calculated_graph) {
                setGraphData(result.calculated_graph);
            }
        } catch (err) {
            console.error("Scope 3 Analysis failed:", err);
            setAiText("Failed to analyze Scope 3 data. Please check your files and try again.");
        } finally {
            setLoading(false);
        }
    };

    const hasData = graphData.nodes && graphData.nodes.length > 0;

    return (
        <div>
            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Scope 3 Visualization</h1>
                    <p className="page-sub">Supply chain network graph with AI-powered risk reasoning</p>
                </div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                        {esgFile ? '✅ ESG Report' : '📁 Upload ESG'}
                        <input type="file" accept=".pdf" style={{ display: 'none' }}
                            onChange={(e) => setEsgFile(e.target.files[0])} />
                    </label>
                    <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                        {supplierFile ? '✅ Manifest' : '📁 Upload Manifest'}
                        <input type="file" accept=".csv,.xlsx,.pdf" style={{ display: 'none' }}
                            onChange={(e) => setSupplierFile(e.target.files[0])} />
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
            </div>

            {/* Graph */}
            <div className="card mb-24">
                <div className="card-title mb-16">Supply Chain Network</div>
                {hasData ? (
                    <NetworkGraph nodes={graphData.nodes} edges={graphData.edges} />
                ) : (
                    <div className="empty-state py-40 text-center">
                        <div className="empty-icon mb-16" style={{ fontSize: '48px' }}>🌐</div>
                        <h3>No Data Visualized</h3>
                        <p className="text-muted">Upload your ESG report and supplier manifest to generate your supply chain network map.</p>
                    </div>
                )}
            </div>

            {/* Stats row */}
            <div className="stats-grid mb-24">
                {[
                    { icon: '🔗', value: graphData.summary?.total_suppliers || '0', label: 'Total Suppliers' },
                    { icon: '👁️', value: graphData.summary?.disclosed || '0', label: 'Disclosed' },
                    { icon: '🕵️', value: graphData.summary?.hidden || '0', label: 'Hidden/Undisclosed' },
                    { icon: '📦', value: `${graphData.summary?.total_emissions_tco2e || '0'}`, label: 'Total tCO2e (calc)' },
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
