import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS, CategoryScale, LinearScale,
    BarElement, Tooltip, Legend,
} from 'chart.js';
import RiskGauge from '../components/RiskGauge';
import AuditTimeline from '../components/AuditTimeline';
import { getDashboardStats, getAuditLog } from '../api/api';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

// ── Mock machine data (used as fallback) ────────────────────────
const MOCK_MACHINES = [
    { machine_id: 'M-001', type: 'Heavy Press', energy_source: 'Grid Electric', co2_kg: 1842, kwh_consumed: 1840, anomaly: true, anomaly_reason: 'Operating 2.8x above baseline' },
    { machine_id: 'M-002', type: 'CNC Milling Center', energy_source: 'Grid Electric', co2_kg: 631, kwh_consumed: 620, anomaly: false, anomaly_reason: null },
    { machine_id: 'M-003', type: 'Paint Booth', energy_source: 'Natural Gas', co2_kg: 478, kwh_consumed: 390, anomaly: false, anomaly_reason: null },
    { machine_id: 'M-004', type: 'Assembly Robot Arm', energy_source: 'Grid Electric', co2_kg: 892, kwh_consumed: 880, anomaly: true, anomaly_reason: 'Operating 1.9x above baseline' },
    { machine_id: 'M-005', type: 'Air Compressor', energy_source: 'Compressed Air', co2_kg: 312, kwh_consumed: 480, anomaly: false, anomaly_reason: null },
];

const MOCK_STATS = {
    esg_score: 78, e_score: 82, s_score: 74, g_score: 79,
    co2_reported: '12,400', risk_flags: 3, farmer_matches: 12,
    recent_analyses: [
        { company: 'TechCorp Industries', score: 82, status: 'Clean', date: '2024-05-10' },
        { company: 'MegaSupply Co.', score: 41, status: 'Flagged', date: '2024-04-28' },
        { company: 'EcoLogistics Ltd', score: 76, status: 'Clean', date: '2024-04-15' },
        { company: 'FastChain Inc.', score: 33, status: 'Critical', date: '2024-03-30' },
    ],
};

const STATUS_BADGE = { Clean: 'badge-green', Flagged: 'badge-yellow', Critical: 'badge-red' };

// ── Runtime hours labels ─────────────────────────────────────────
const HOURS = ['06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'];
const MACHINE_COLORS = ['#00f5a0', '#00d4ff', '#ffd166', '#ff4d6d', '#a78bfa'];

function getMachineStatusStyle(machine) {
    if (machine.anomaly) {
        return {
            border: '2px solid #ff4d6d',
            boxShadow: '0 0 18px rgba(255,77,109,0.35)',
            background: 'rgba(255,77,109,0.06)',
        };
    }
    if (machine.co2_kg < 500) {
        return {
            border: '2px solid #00f5a0',
            boxShadow: '0 0 12px rgba(0,245,160,0.2)',
        };
    }
    return {
        border: '2px solid rgba(255,193,7,0.5)',
        boxShadow: '0 0 8px rgba(255,193,7,0.15)',
    };
}

function MachineCard({ machine, index }) {
    const statusStyle = getMachineStatusStyle(machine);
    const isAnomaly = machine.anomaly;
    const emissionColor = isAnomaly ? '#ff4d6d' : (machine.co2_kg < 500 ? '#00f5a0' : '#ffd166');
    const statusLabel = isAnomaly ? '⚠️ Anomaly' : (machine.co2_kg < 500 ? '✅ Optimal' : '🟡 Monitor');

    return (
        <div style={{
            ...statusStyle,
            borderRadius: '14px',
            padding: '18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            position: 'relative',
            transition: 'box-shadow 0.3s',
        }}>
            {/* Pulse dot for anomalies */}
            {isAnomaly && (
                <span style={{
                    position: 'absolute', top: '14px', right: '14px',
                    width: '10px', height: '10px', borderRadius: '50%',
                    background: '#ff4d6d',
                    animation: 'pulse-ring 1.4s ease infinite',
                    display: 'block',
                }} />
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                        {machine.machine_id}
                    </div>
                    <div style={{ fontSize: '15px', fontWeight: 700, marginTop: '2px' }}>{machine.type}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{machine.energy_source}</div>
                </div>
                <div style={{
                    fontSize: '11px', fontWeight: 600, padding: '4px 10px',
                    borderRadius: '20px',
                    background: isAnomaly ? 'rgba(255,77,109,0.15)' : (machine.co2_kg < 500 ? 'rgba(0,245,160,0.12)' : 'rgba(255,209,102,0.12)'),
                    color: emissionColor,
                }}>
                    {statusLabel}
                </div>
            </div>

            {/* Telemetry metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '4px' }}>
                {[
                    { label: 'CO₂ Emitted', value: `${machine.co2_kg} kg`, color: emissionColor },
                    { label: 'Power Draw', value: `${machine.kwh_consumed} kWh`, color: 'var(--accent-2)' },
                ].map(m => (
                    <div key={m.label} style={{
                        background: 'rgba(255,255,255,0.04)', borderRadius: '8px',
                        padding: '8px 10px',
                    }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '2px' }}>{m.label}</div>
                        <div style={{ fontSize: '16px', fontWeight: 700, color: m.color }}>{m.value}</div>
                    </div>
                ))}
            </div>

            {/* Anomaly banner */}
            {isAnomaly && (
                <div style={{
                    background: 'rgba(255,77,109,0.1)', border: '1px solid rgba(255,77,109,0.25)',
                    borderRadius: '8px', padding: '8px 10px',
                    fontSize: '11.5px', color: '#ff8fa3',
                }}>
                    ⚡ {machine.anomaly_reason}
                </div>
            )}

            {/* Mini emission bar */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    <span>Emission intensity</span>
                    <span style={{ color: emissionColor }}>
                        {Math.round((machine.co2_kg / 2500) * 100)}%
                    </span>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '99px', height: '4px' }}>
                    <div style={{
                        width: `${Math.min(100, (machine.co2_kg / 2500) * 100)}%`,
                        background: emissionColor, height: '4px', borderRadius: '99px',
                        transition: 'width 0.8s ease',
                    }} />
                </div>
            </div>
        </div>
    );
}

function buildStackedChartData(machines) {
    // Simulate 8 hourly readings slightly varied per machine
    const datasets = machines.map((m, i) => ({
        label: `${m.machine_id} — ${m.type.split(' ')[0]}`,
        data: HOURS.map((_, hi) =>
            Math.round(m.co2_kg / 8 * (0.7 + Math.sin(hi * 0.9 + i) * 0.3))
        ),
        backgroundColor: MACHINE_COLORS[i % MACHINE_COLORS.length] + 'cc',
        borderColor: MACHINE_COLORS[i % MACHINE_COLORS.length],
        borderWidth: 1,
        borderRadius: 4,
        stack: 'emissions',
    }));
    return { labels: HOURS, datasets };
}

const CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#b0bec5', font: { family: 'Inter', size: 11 } } },
        tooltip: {
            mode: 'index',
            callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y} kgCO₂` },
        },
    },
    scales: {
        x: { stacked: true, ticks: { color: '#7a8aaa' }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: {
            stacked: true,
            ticks: { color: '#7a8aaa', callback: (v) => `${v} kg` },
            grid: { color: 'rgba(255,255,255,0.04)' },
        },
    },
};

export default function CompanyDashboard() {
    const [stats, setStats] = useState(null);
    const [audit, setAudit] = useState(null);
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);

    const s = stats;
    // M5 FIX: isNewUser only if no analyses have ever been run, regardless of score
    const isNewUser = !s || (!s.recent_analyses?.length && s.esg_score === 0);

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [statsRes, auditRes] = await Promise.all([
                    getDashboardStats(),
                    getAuditLog(),
                ]);
                setStats(statsRes.data);
                setAudit(auditRes.data);
                if (statsRes.data.machine_data?.length) setMachines(statsRes.data.machine_data);
            } catch {
                setStats(null);
            } finally {
                setLoading(false);
            }
        };

        fetchAll(); // Initial load
        const interval = setInterval(fetchAll, 5000); // Polling for real-time demo
        return () => clearInterval(interval);
    }, []);

    const STAT_CARDS = [
        { icon: '📊', value: isNewUser ? '—' : s.esg_score, label: 'ESG Score', change: isNewUser ? 'Needs Audit' : 'Live Gemini AI', up: true },
        { icon: '🌍', value: isNewUser ? '0' : s.co2_reported, label: 'tCO₂ Reported', change: isNewUser ? 'No data' : 'Verified', up: true },
        { icon: '⚠️', value: isNewUser ? '0' : (s.risk_flags || 0), label: 'Risk Score', change: isNewUser ? 'System Clean' : `Forensic level: ${s.risk_flags}`, up: false },
        { icon: '🤝', value: isNewUser ? '0' : s.farmer_matches, label: 'Offset Projects', change: isNewUser ? 'None active' : `${s.farmer_matches} matched`, up: true },
    ];

    if (!loading && isNewUser) {
        return (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
                <style>{`
                    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
                `}</style>
                <div className="page-header">
                    <h1 className="page-title">Welcome to Regenera Ledger</h1>
                    <p className="page-sub">AI-Powered ESG Intelligence & Carbon Transparency</p>
                </div>

                <div className="card" style={{ textAlign: 'center', padding: '60px 20px', background: 'rgba(0,245,160,0.03)', border: '1px dashed var(--accent)' }}>
                    <div style={{ fontSize: '48px', marginBottom: '20px' }}>🏭</div>
                    <h2 style={{ marginBottom: '12px' }}>Analyze your first ESG report</h2>
                    <p style={{ color: 'var(--text-muted)', maxWidth: '540px', margin: '0 auto 30px' }}>
                        Upload your company's ESG documents or supplier records. Our Gemini AI will extract metrics, identify risks, and map your Scope 3 emissions automatically.
                    </p>
                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                        <Link to="/esg-analysis" className="btn btn-primary btn-lg">⚡ Run First Analysis</Link>
                        <Link to="/scope3" className="btn btn-secondary btn-lg">🌐 Map Supply Chain</Link>
                    </div>
                </div>

                <div className="grid-3 mt-24">
                    {[
                        { title: '1. ESG Analysis', desc: 'Upload PDFs to get an AI-powered breakdown of your E, S, and G scores.', icon: '🔬' },
                        { title: '2. Carbon Gap', desc: 'Identify emissions that cannot be reduced and need offsetting.', icon: '📉' },
                        { title: '3. Farmer Match', desc: 'Connect with verified sustainable farmers to purchase carbon credits.', icon: '🌱' },
                    ].map(step => (
                        <div key={step.title} className="card">
                            <div style={{ fontSize: '24px', marginBottom: '12px' }}>{step.icon}</div>
                            <div style={{ fontWeight: 700, marginBottom: '8px' }}>{step.title}</div>
                            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{step.desc}</div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    const currentStats = s || { esg_score: 0, e_score: 0, s_score: 0, g_score: 0 };
    const chartData = machines.length > 0 ? buildStackedChartData(machines) : { labels: [], datasets: [] };

    return (
        <div>
            {/* Pulse animation keyframe injected once */}
            <style>{`
        @keyframes pulse-ring {
          0%,100% { opacity:1; transform:scale(1);   box-shadow:0 0 0 0 rgba(255,77,109,0.7); }
          50%      { opacity:.8; transform:scale(1.4); box-shadow:0 0 0 8px rgba(255,77,109,0); }
        }
      `}</style>

            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Macro Digital Twin</h1>
                    <p className="page-sub">Live machine-level ESG intelligence powered by Gemini AI</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <Link to="/esg-analysis" className="btn btn-primary">⚡ Run Analysis</Link>
                    <Link to="/matching" className="btn btn-secondary">🌿 Offset Market</Link>
                </div>
            </div>

            {/* Stat cards */}
            <div className="stats-grid">
                {STAT_CARDS.map((s) => (
                    loading
                        ? <div key={s.label} className="stat-card"><div className="skeleton" style={{ height: '80px' }} /></div>
                        : (
                            <div className="stat-card" key={s.label}>
                                <span className="stat-icon">{s.icon}</span>
                                <span className="stat-value">{s.value}</span>
                                <span className="stat-label">{s.label}</span>
                                <span className={`stat-change${s.up ? '' : ' down'}`}>{s.change}</span>
                            </div>
                        )
                ))}
            </div>

            {/* ── Machine Cards Grid ── */}
            <div className="section-title" style={{ marginTop: '28px' }}>
                🏭 Live Machine Telemetry
                <span style={{ fontSize: '12px', fontWeight: 400, color: 'var(--text-muted)', marginLeft: '12px' }}>
                    {machines.filter(m => m.anomaly).length} anomalies detected
                </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))', gap: '16px', marginBottom: '28px' }}>
                {loading ? (
                    [1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: '180px', borderRadius: '14px' }} />)
                ) : machines.length > 0 ? (
                    machines.map((m, i) => <MachineCard key={m.machine_id} machine={m} index={i} />)
                ) : (
                    <div className="card col-span-full" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                        <div>📡 No machine telemetry detected yet.</div>
                        <div style={{ fontSize: '13px', marginTop: '8px' }}>
                            Machine-level ESG data will appear here once you've completed your first audit or integrated your IoT sensors.
                        </div>
                    </div>
                )}
            </div>

            {/* ── Stacked Bar Chart ── */}
            <div className="card mb-24">
                <div className="card-title">Machine Emission Contributions Over Time</div>
                <div className="card-desc mb-16">Stacked CO₂ output per machine across today's operating hours</div>
                <div style={{ height: '300px', position: 'relative' }}>
                    <Bar data={chartData} options={CHART_OPTIONS} />
                </div>
            </div>

            {/* ESG Gauge + Quick Actions */}
            <div className="grid-2 mb-24">
                <div className="card">
                    <div className="card-title">Overall ESG Score</div>
                    <div className="card-desc mb-16">Aggregated from Digital Twin analysis</div>
                    {loading
                        ? <div className="skeleton" style={{ height: '160px' }} />
                        : <RiskGauge score={currentStats.esg_score || 0} label="ESG Score" />
                    }
                    <div style={{ marginTop: '16px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        <span className="badge badge-green">E: {currentStats.e_score || 0}</span>
                        <span className="badge badge-blue">S: {currentStats.s_score || 0}</span>
                        <span className="badge badge-yellow">G: {currentStats.g_score || 0}</span>
                    </div>
                </div>
                <div className="card flex flex-col gap-12">
                    <div className="card-title">Quick Actions</div>
                    {[
                        { icon: '🔬', label: 'Full ESG Audit', to: '/esg-analysis', color: 'btn-primary' },
                        { icon: '🌐', label: 'Scope 3 Supply Map', to: '/scope3', color: 'btn-secondary' },
                        { icon: '📉', label: 'Carbon Gap Report', to: '/carbon-gap', color: 'btn-secondary' },
                        { icon: '🌿', label: 'Carbon Marketplace', to: '/matching', color: 'btn-secondary' },
                    ].map(a => (
                        <Link key={a.to} to={a.to} className={`btn ${a.color}`} style={{ justifyContent: 'flex-start' }}>
                            {a.icon} {a.label}
                        </Link>
                    ))}
                </div>
            </div>

            {/* ── Recent Analyses Table ── */}
            <div className="section-title" style={{ marginTop: '28px' }}>🔍 Recent AI Analyses</div>
            <div className="card mb-24">
                <div className="table-container">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Project / Report</th>
                                <th>ESG Score</th>
                                <th>Status</th>
                                <th>Date</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="5" className="text-center">Loading analyses...</td></tr>
                            ) : s?.recent_analyses?.length > 0 ? (
                                s.recent_analyses.map((ra, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 600 }}>{ra.company || ra.filename || 'ESG Report'}</td>
                                        <td>
                                            <span style={{
                                                fontWeight: 700,
                                                color: ra.score >= 70 ? '#00f5a0' : (ra.score >= 40 ? '#ffd166' : '#ff4d6d')
                                            }}>
                                                {ra.score}
                                            </span>
                                        </td>
                                        <td>
                                            <span className={`badge ${ra.status === 'Clean' ? 'badge-green' : (ra.status === 'Flagged' ? 'badge-yellow' : 'badge-red')}`}>
                                                {ra.status}
                                            </span>
                                        </td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{ra.date}</td>
                                        <td>
                                            <Link to="/esg-analysis" className="btn btn-secondary btn-sm" style={{ padding: '4px 10px', fontSize: '11px' }}>
                                                View Report
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr><td colSpan="5" className="text-center" style={{ color: 'var(--text-muted)', padding: '30px' }}>No analyses found. Run your first audit to see results here.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Audit Timeline */}
            <div className="section-title">Audit History</div>
            <div className="card">
                <AuditTimeline events={audit || undefined} />
            </div>
        </div>
    );
}
