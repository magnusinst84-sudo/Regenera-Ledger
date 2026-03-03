import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import RiskGauge from '../components/RiskGauge';
import { getFarmerDashboard } from '../api/api';

const MOCK = {
    credits_earned: '4,200',
    earnings: '₹35.7L',
    active_matches: 3,
    acres: 42,
    credibility: 88,
    credit_history: [
        { season: 'Kharif 2024', crop: 'Rice', credits: 240, status: 'Verified', value: '₹1.72L' },
        { season: 'Rabi 2024', crop: 'Wheat', credits: 180, status: 'Pending', value: '₹1.3L' },
        { season: 'Kharif 2023', crop: 'Rice', credits: 220, status: 'Verified', value: '₹1.54L' },
    ],
    matches: [
        { name: 'Regenera Ledger Corp', credits: 240, status: 'Matched', color: 'badge-green' },
        { name: 'TechCorp Industries', credits: 180, status: 'Pending', color: 'badge-yellow' },
        { name: 'EcoLogistics Ltd', credits: 310, status: 'Declined', color: 'badge-red' },
    ],
};

const STATUS_BADGE = { Verified: 'badge-green', Pending: 'badge-yellow' };

export default function FarmerDashboard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getFarmerDashboard()
            .then((res) => setData(res.data))
            .catch(() => setData(null))
            .finally(() => setLoading(false));
    }, []);

    const d = data || {};
    // User is "new" if we have no profile ID or name, AND no land/credits
    const hasProfile = d && (d.id || d.name);
    const hasData = d && (parseFloat(d.acres) > 0 || parseFloat(d.credits_earned) > 0);
    const isNewUser = !hasProfile || !hasData;

    const STATS = [
        { icon: '🌱', value: isNewUser ? '0' : (d.credits_earned || 0), label: 'tCO₂ Credits Earned' },
        { icon: '💰', value: isNewUser ? '₹0' : (d.earnings || 0), label: 'Total Earnings' },
        { icon: '🤝', value: isNewUser ? '0' : (d.active_matches || 0), label: 'Active Matches' },
        { icon: '🌾', value: isNewUser ? '0' : (d.acres || 0), label: 'Acres Enrolled' },
    ];

    if (!loading && isNewUser) {
        return (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
                <div className="page-header">
                    <h1 className="page-title">Welcome to Regenera Ledger</h1>
                    <p className="page-sub">Your journey to earning carbon credits starts here.</p>
                </div>

                <div className="card" style={{ textAlign: 'center', padding: '60px 20px', background: 'linear-gradient(135deg, rgba(0,245,160,0.05) 0%, rgba(0,212,255,0.05) 100%)', border: '1px dashed var(--accent)' }}>
                    <div style={{ fontSize: '48px', marginBottom: '20px' }}>🚜</div>
                    <h2 style={{ marginBottom: '12px' }}>Ready to monetize your sustainable farming?</h2>
                    <p style={{ color: 'var(--text-muted)', maxWidth: '500px', margin: '0 auto 30px' }}>
                        Complete your profile with your land details and sustainable practices to start generating verified carbon credits that companies can purchase.
                    </p>
                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                        <Link to="/farmer/profile" className="btn btn-primary btn-lg">👤 Complete My Profile</Link>
                        <Link to="/farmer/estimate" className="btn btn-secondary btn-lg">💰 Try Estimation</Link>
                    </div>
                </div>

                <div className="grid-3 mt-24">
                    {[
                        { title: '1. Update Profile', desc: 'Add land size and practices like no-till or organic composting.', icon: '📝' },
                        { title: '2. Get Estimated', desc: 'Use our Gemini AI to estimate how much carbon your land stores.', icon: '🤖' },
                        { title: '3. Get Matched', desc: 'Once verified, your credits appear on the market for companies.', icon: '🤝' },
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

    const currentData = d || { credibility: 0, matches: [], credit_history: [] };

    return (
        <div>
            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Farmer Dashboard</h1>
                    <p className="page-sub">Track your carbon credits, earnings, and company matches</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <Link to="/farmer/estimate" className="btn btn-primary">💰 Estimate Credits</Link>
                    <Link to="/farmer/profile" className="btn btn-secondary">👤 My Profile</Link>
                </div>
            </div>

            {/* Stats */}
            <div className="stats-grid">
                {STATS.map((s) => (
                    <div className="stat-card" key={s.label}>
                        {loading
                            ? <div className="skeleton" style={{ height: '80px' }} />
                            : <>
                                <span className="stat-icon">{s.icon}</span>
                                <span className="stat-value">{s.value}</span>
                                <span className="stat-label">{s.label}</span>
                            </>
                        }
                    </div>
                ))}
            </div>

            <div className="grid-2 mb-24">
                {/* Credibility Gauge */}
                <div className="card">
                    <div className="card-title">Credibility Score</div>
                    <div className="card-desc mb-16">Based on verified carbon practices</div>
                    {loading
                        ? <div className="skeleton" style={{ height: '160px' }} />
                        : <RiskGauge score={currentData.credibility || 0} label="Credibility" />
                    }
                    <div style={{ marginTop: '12px' }}>
                        {[['Sustainable practices', 0], ['Documentation completeness', 0], ['Third-party verification', 0]].map(([label, pct]) => {
                            const actualPct = currentData.credibility ? (label === 'Sustainable practices' ? 92 : label === 'Documentation completeness' ? 85 : 78) : 0;
                            return (
                                <div key={label} style={{ marginBottom: '10px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                                        <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{actualPct}%</span>
                                    </div>
                                    <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '99px', height: '5px' }}>
                                        <div style={{ width: `${actualPct}%`, background: 'linear-gradient(90deg, var(--accent), var(--accent-2))', height: '5px', borderRadius: '99px' }} />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Matches */}
                <div className="card flex flex-col gap-12">
                    <div className="card-title">Company Matches</div>
                    {currentData.matches && currentData.matches.length > 0 ? (
                        currentData.matches.map((m) => (
                            <div key={m.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '13.5px' }}>{m.name}</div>
                                    <div className="text-muted text-sm">{m.credits} tCO₂ requested</div>
                                </div>
                                <span className={`badge ${m.color}`}>{m.status}</span>
                            </div>
                        ))
                    ) : (
                        <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)', fontSize: '13px' }}>
                            No active matches found. Once your credits are verified, companies can find you here.
                        </div>
                    )}
                </div>
            </div>

            {/* Credit History */}
            <div className="section-title">Credit History</div>
            <div className="table-wrap">
                <table className="table">
                    <thead>
                        <tr><th>Season</th><th>Crop</th><th>Credits (tCO₂)</th><th>Status</th><th>Est. Value</th></tr>
                    </thead>
                    <tbody>
                        {currentData.credit_history && currentData.credit_history.length > 0 ? (
                            currentData.credit_history.map((c) => (
                                <tr key={c.season}>
                                    <td style={{ fontWeight: 500 }}>{c.season}</td>
                                    <td>{c.crop}</td>
                                    <td style={{ color: 'var(--accent)', fontWeight: 600 }}>{c.credits}</td>
                                    <td><span className={`badge ${STATUS_BADGE[c.status]}`}>{c.status}</span></td>
                                    <td style={{ color: 'var(--text-2)' }}>{c.value}</td>
                                </tr>
                            ))
                        ) : (
                            <tr><td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                                No credit history available yet. Try running an estimation to see your potential!
                            </td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
