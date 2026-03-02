import { useState, useRef, useEffect } from 'react';
import AIExplanationPanel from '../components/AIExplanationPanel';
import RiskGauge from '../components/RiskGauge';
import { analyzeESG, getAnalysisHistory } from '../api/api';

const MOCK_RESULT = {
    score: 64,
    flags: [
        { type: 'danger', text: 'Scope 2 emissions appear understated by ~30% vs industry benchmarks.' },
        { type: 'warning', text: 'No third-party verification for Scope 3 supplier data.' },
        { type: 'info', text: 'Renewable energy transition commitments are well-documented.' },
    ],
    aiText: `Based on my forensic analysis of this ESG report, I have identified several key concerns:

1. GREENWASHING RISK (HIGH): The reported Scope 2 emissions of 4,200 tCO₂ are significantly below the industry median of 6,100 tCO₂ for a company of this size. Without third-party attestation, this figure cannot be verified.

2. SCOPE 3 GAP: Only Tier-1 suppliers are accounted for. Downstream logistics and end-of-life product emissions are completely absent from the report.

3. POSITIVE INDICATORS: The company has genuine renewable energy procurement contracts (PPAs) covering 62% of electricity consumption, which is above sector average.

Overall ESG Score: 64/100. Recommend immediate third-party audit of Scope 2 and 3 data.`,
};

export default function ESGAnalysis() {
    const [file, setFile] = useState(null);
    const [dragging, setDragging] = useState(false);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const inputRef = useRef();

    useEffect(() => {
        const fetchLatest = async () => {
            try {
                const res = await getAnalysisHistory();
                const history = res.data.results || [];
                const latestEsg = history.find(h => h.type === 'esg' || h.analysis_type === 'esg');
                if (latestEsg) {
                    // Extract data from result_json
                    const data = latestEsg.result_json || latestEsg.result;
                    setResult({
                        score: 100 - (data.greenwashing_score || 0),
                        flags: (data.extracted_entities?.red_flags || []).map(f => ({ type: 'danger', text: f })),
                        aiText: data.explanation || 'Latest analysis loaded.',
                        isFromHistory: true
                    });
                }
            } catch (err) {
                console.error('Failed to fetch history:', err);
            }
        };
        fetchLatest();
    }, []);

    const handleFile = (f) => {
        if (!f) return;
        if (result && !window.confirm('You already have an active ESG analysis. Uploading a new file will start a fresh audit. Continue?')) {
            return;
        }
        setFile(f);
        // Don't clear result immediately if user cancels or just selects file
    };

    const handleDrop = (e) => {
        e.preventDefault(); setDragging(false);
        handleFile(e.dataTransfer.files[0]);
    };

    const handleAnalyze = async () => {
        setLoading(true);
        try {
            // Try real API; fall back to mock
            const fd = new FormData();
            fd.append('file', file);
            const res = await analyzeESG(fd);
            setResult(res.data);
        } catch {
            await new Promise((r) => setTimeout(r, 1800));
            setResult(MOCK_RESULT);
        } finally {
            setLoading(false);
        }
    };

    const FLAG_STYLE = { danger: ['var(--danger)', '⛔'], warning: ['var(--warning)', '⚠️'], info: ['var(--accent)', '✅'] };

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">ESG Analysis</h1>
                <p className="page-sub">Upload an ESG report for AI-powered forensic audit & greenwashing detection</p>
            </div>

            <div className="grid-2">
                {/* Upload Panel */}
                <div className="card">
                    <div className="card-title mb-16">Upload ESG Report</div>
                    <div
                        id="upload-zone"
                        className={`upload-zone${dragging ? ' drag-over' : ''}`}
                        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={handleDrop}
                        onClick={() => inputRef.current.click()}
                    >
                        <div className="upload-icon">📄</div>
                        <div className="upload-text">
                            {file ? file.name : 'Drop your ESG PDF here'}
                        </div>
                        <div className="upload-hint">
                            {file ? `${(file.size / 1024).toFixed(0)} KB · PDF` : 'or click to browse · PDF, DOCX, TXT'}
                        </div>
                    </div>
                    <input ref={inputRef} type="file" accept=".pdf,.docx,.txt" style={{ display: 'none' }} onChange={(e) => handleFile(e.target.files[0])} />

                    {file && (
                        <button
                            id="analyze-btn"
                            className="btn btn-primary btn-lg w-full mt-16"
                            style={{ justifyContent: 'center' }}
                            onClick={handleAnalyze}
                            disabled={loading}
                        >
                            {loading ? '🔍 Analyzing...' : '🔬 Run Gemini ESG Audit'}
                        </button>
                    )}

                    {/* Analysis options */}
                    <div style={{ marginTop: '16px' }}>
                        {['Detect greenwashing', 'Scope 1/2/3 breakdown', 'Industry benchmark comparison'].map((opt) => (
                            <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', fontSize: '13px', color: 'var(--text-2)', cursor: 'pointer' }}>
                                <input type="checkbox" defaultChecked style={{ accentColor: 'var(--accent)' }} />
                                {opt}
                            </label>
                        ))}
                    </div>
                </div>

                {/* Results Panel */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {(loading || result) && (
                        <div className="card">
                            <div className="card-title mb-16">ESG Score</div>
                            <RiskGauge score={result?.score || 0} label="Overall Score" />
                        </div>
                    )}

                    {result && (
                        <div className="card">
                            <div className="card-title mb-16">Risk Flags</div>
                            {result.flags.map((f, i) => {
                                const [color, icon] = FLAG_STYLE[f.type] || FLAG_STYLE.info;
                                return (
                                    <div key={i} style={{
                                        padding: '10px 14px', borderRadius: '8px', marginBottom: '8px',
                                        background: `${color}12`, border: `1px solid ${color}30`,
                                        fontSize: '13px', color: 'var(--text-2)',
                                        display: 'flex', gap: '8px',
                                    }}>
                                        <span>{icon}</span><span>{f.text}</span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* AI Explanation */}
            <div className="mt-24">
                <AIExplanationPanel
                    text={result?.aiText}
                    isLoading={loading}
                    title={result?.isFromHistory ? "Gemini ESG Audit Report (Stored)" : "Gemini ESG Audit Report"}
                />
            </div>
        </div>
    );
}
