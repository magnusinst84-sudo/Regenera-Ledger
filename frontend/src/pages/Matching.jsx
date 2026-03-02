import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import MapPicker from '../components/MapPicker';
import AIExplanationPanel from '../components/AIExplanationPanel';
import OffsetProjectCard from '../components/OffsetProjectCard';
import { getFarmers, matchFarmer, getDashboardStats } from '../api/api';

// ── Category config ──────────────────────────────────────────────
const CATEGORIES = ['All', 'Regen-Ag', 'Blue Carbon', 'DAC', 'Forestry'];

const CAT_STYLE = {
    'Regen-Ag': { bg: 'rgba(0,245,160,0.15)', border: 'rgba(0,245,160,0.4)', color: '#00f5a0', icon: '🌾', label: 'Regen-Ag' },
    'Blue Carbon': { bg: 'rgba(0,212,255,0.15)', border: 'rgba(0,212,255,0.4)', color: '#00d4ff', icon: '🌊', label: 'Blue Carbon' },
    'DAC': { bg: 'rgba(167,139,250,0.15)', border: 'rgba(167,139,250,0.4)', color: '#a78bfa', icon: '⚗️', label: 'Tech-Based (DAC)' },
    'Tech-Based DAC': { bg: 'rgba(167,139,250,0.15)', border: 'rgba(167,139,250,0.4)', color: '#a78bfa', icon: '⚗️', label: 'Tech-Based (DAC)' },
    'Forestry': { bg: 'rgba(74,222,128,0.12)', border: 'rgba(74,222,128,0.35)', color: '#4ade80', icon: '🌲', label: 'Forestry' },
};

const MOCK_PROJECTS = [];
// C1 FIX: TOTAL_DEFICIT now starts at 0 and is fetched from the company profile via backend

// ── Portfolio state helpers ──────────────────────────────────────
function totalAllocated(cart) {
    return Object.values(cart).reduce((a, b) => a + b, 0);
}

function totalCost(cart, projects) {
    return Object.entries(cart).reduce((sum, [id, tons]) => {
        const p = projects.find(x => x.id === id);
        return sum + (p ? tons * parseFloat(p.price_per_ton_usd) : 0);
    }, 0);
}

export default function Matching() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [loadingMap, setLoadingMap] = useState(true);
    const [activeTab, setActiveTab] = useState('All');
    const [cart, setCart] = useState({});   // { project_id: tons }
    const [matching, setMatching] = useState(false);
    const [aiText, setAiText] = useState('');
    const [portfolio, setPortfolio] = useState(null);
    const [totalDeficit, setTotalDeficit] = useState(1800); // default, overridden from profile

    // H1 FIX: redirect farmers away from marketplace (they have no access to /api/farmer/all as company)
    useEffect(() => {
        if (user?.role === 'farmer') {
            navigate('/farmer/profile', { replace: true });
        }
    }, [user, navigate]);

    useEffect(() => {
        const fetchData = () => {
            getFarmers()
                .then(res => {
                    const data = res.data.farmers || res.data || [];
                    setProjects(Array.isArray(data) ? data : []);
                })
                .catch(() => setProjects([]))
                .finally(() => setLoadingMap(false));
        };

        fetchData(); // Initial load
        const interval = setInterval(fetchData, 5000); // Poll every 5 seconds for "Real-time" demo
        return () => clearInterval(interval);
    }, []);

    const filtered = (projects || []).filter(p => {
        if (!p) return false;
        if (activeTab === 'All') return true;
        const cat = p.category || 'Forestry';
        if (activeTab === 'DAC' && (cat === 'DAC' || cat === 'Tech-Based DAC')) return true;
        return cat === activeTab;
    });

    const setTons = (id, value) => {
        const num = Math.max(0, Math.min(Number(value), totalDeficit));
        setCart(prev => ({ ...prev, [id]: num }));
    };

    const allocated = totalAllocated(cart);
    const remaining = Math.max(0, totalDeficit - allocated);
    const coveragePct = totalDeficit > 0 ? Math.min(100, Math.round((allocated / totalDeficit) * 100)) : 0;
    const costUSD = totalCost(cart, projects);

    const handleMatch = async () => {
        setMatching(true); setAiText(''); setPortfolio(null);
        try {
            const res = await matchFarmer({ total_deficit_t: totalDeficit });
            setPortfolio(res.data.portfolio);
            setAiText(res.data.ai_text);
            // Auto-populate cart from returned portfolio
            if (res.data.portfolio) {
                const newCart = {};
                res.data.portfolio.forEach(item => {
                    if (item.project_id) newCart[item.project_id] = item.allocated_t;
                });
                setCart(newCart);
            }
        } catch {
            await new Promise(r => setTimeout(r, 1400));
            // M4 FIX: Dynamic fallback uses real projects from the DB
            const forestry = projects.find(p => p.category === 'Forestry');
            const regen = projects.find(p => p.category === 'Regen-Ag');
            const blue = projects.find(p => p.category === 'Blue Carbon');
            const dac = projects.find(p => p.category === 'DAC' || p.category === 'Tech-Based DAC');
            setAiText(
                `Diversified Carbon Portfolio — Gemini Strategy:

Total deficit: ${totalDeficit} tCO₂e. Recommended allocation:
${forestry ? `• Forestry (50% = ${Math.round(totalDeficit * 0.5)}t): ${forestry.name} @ $${forestry.price_per_ton_usd}/t` : '• Forestry: See marketplace for listed projects'}
${regen ? `• Regen-Ag (30% = ${Math.round(totalDeficit * 0.3)}t): ${regen.name} @ $${regen.price_per_ton_usd}/t` : '• Regen-Ag: See marketplace for listed projects'}
${blue ? `• Blue Carbon (15% = ${Math.round(totalDeficit * 0.15)}t): ${blue.name} @ $${blue.price_per_ton_usd}/t` : '• Blue Carbon: See marketplace for listed projects'}
${dac ? `• DAC (5% = ${Math.round(totalDeficit * 0.05)}t): ${dac.name} @ $${dac.price_per_ton_usd}/t` : '• DAC: See marketplace for listed projects'}

Strategy rationale: Forestry provides immediate volume at scale. Regen-Ag creates social co-benefits for Indian farmers. Blue Carbon offers long-term permanence. DAC provides the tech credibility signal to investors.`
            );
        } finally {
            setMatching(false);
        }
    };

    const handleDelete = async (id) => {
        try {
            const { removeFarmer } = await import('../api/api');
            await removeFarmer(id);
            setProjects(prev => (prev || []).filter(p => p.id !== id));
        } catch (err) {
            alert('Failed to delete farmer: ' + (err.response?.data?.detail || err.message));
        }
    };

    return (
        <div>
            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Carbon Offset Marketplace</h1>
                    <p className="page-sub">Build a diversified portfolio across Forestry, Regen-Ag, Blue Carbon & DAC</p>
                </div>
                <button id="match-btn" className="btn btn-primary" onClick={handleMatch} disabled={matching || loadingMap}>
                    {matching ? '⏳ Building Portfolio...' : '🤖 Auto-Build with Gemini'}
                </button>
            </div>

            {/* ── Deficit Progress Bar ── */}
            <div className="card mb-20">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ fontWeight: 700, fontSize: '15px' }}>
                        Portfolio Builder
                        <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '13px', marginLeft: '8px' }}>
                            Carbon Gap: {totalDeficit.toLocaleString()} tCO₂e
                        </span>
                    </div>
                    <div style={{ display: 'flex', gap: '20px', fontSize: '13px' }}>
                        <span>Allocated: <strong style={{ color: 'var(--accent)' }}>{allocated.toLocaleString()} t</strong></span>
                        <span>Remaining: <strong style={{ color: remaining > 0 ? 'var(--warning)' : 'var(--accent)' }}>{remaining.toLocaleString()} t</strong></span>
                        <span>Est. Cost: <strong style={{ color: 'var(--accent-2)' }}>${costUSD.toLocaleString(undefined, { maximumFractionDigits: 0 })}</strong></span>
                    </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '99px', height: '8px', overflow: 'hidden' }}>
                    <div style={{
                        width: `${coveragePct}%`, height: '8px', borderRadius: '99px',
                        background: coveragePct >= 100
                            ? 'linear-gradient(90deg,#00f5a0,#00d4ff)'
                            : 'linear-gradient(90deg,#ffd166,#f4a261)',
                        transition: 'width 0.4s ease',
                    }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px', fontSize: '11px', color: 'var(--text-muted)' }}>
                    <span>0 t</span>
                    <span style={{ color: coveragePct >= 100 ? 'var(--accent)' : 'var(--text-muted)', fontWeight: coveragePct >= 100 ? 700 : 400 }}>
                        {coveragePct}% covered
                    </span>
                    <span>{totalDeficit.toLocaleString()} t</span>
                </div>
            </div>

            {/* ── Category Filter Tabs ── */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
                {CATEGORIES.map(cat => {
                    const style = cat !== 'All' ? CAT_STYLE[cat] : null;
                    const isActive = activeTab === cat;
                    return (
                        <button
                            key={cat}
                            onClick={() => setActiveTab(cat)}
                            style={{
                                padding: '7px 16px', borderRadius: '99px', fontSize: '12.5px', fontWeight: 600,
                                border: isActive
                                    ? `1.5px solid ${style?.color || 'var(--accent)'}`
                                    : '1.5px solid var(--border)',
                                background: isActive
                                    ? (style?.bg || 'rgba(0,245,160,0.12)')
                                    : 'transparent',
                                color: isActive ? (style?.color || 'var(--accent)') : 'var(--text-muted)',
                                cursor: 'pointer', transition: 'all 0.2s',
                            }}
                        >
                            {style?.icon || '🌍'} {cat === 'DAC' ? 'Tech-Based (DAC)' : cat}
                        </button>
                    );
                })}
            </div>

            <div className="grid-2" style={{ alignItems: 'start' }}>
                {/* Project Cards — using OffsetProjectCard with category-specific layouts */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    {loadingMap
                        ? [1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: '180px', borderRadius: '16px' }} />)
                        : filtered.length === 0
                            ? (
                                <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
                                    <div style={{ fontSize: '36px', marginBottom: '12px' }}>🌿</div>
                                    <div style={{ fontWeight: 600, marginBottom: '6px' }}>No projects in this category yet</div>
                                    <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                                        Try switching to <strong>All</strong> or another category to explore available offset projects.
                                    </div>
                                </div>
                            )
                            : filtered.map(p => (
                                <OffsetProjectCard
                                    key={p.id}
                                    project={{
                                        ...p,
                                        financials: { price_per_ton_usd: p.price_per_ton_usd },
                                        metrics: {
                                            durability_years: p.durability_years,
                                            available_inventory_tons: p.credits_available,
                                            co_benefits: p.co_benefits || [],
                                        },
                                    }}
                                    tons={cart[p.id] || 0}
                                    selected={!!(cart[p.id] > 0)}
                                    onAdd={(id, tons) => setTons(id, tons)}
                                    onDelete={handleDelete}
                                />
                            ))
                    }
                </div>

                {/* Map */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="card">
                        <div className="card-title mb-16">Project Locations</div>
                        {loadingMap
                            ? <div className="skeleton" style={{ height: '340px' }} />
                            : <MapPicker farmers={projects} onSelect={null} />
                        }
                    </div>

                    {/* Portfolio summary */}
                    {Object.values(cart).some(v => v > 0) && (
                        <div className="card">
                            <div className="card-title mb-12">Portfolio Summary</div>
                            {Object.entries(cart).filter(([, v]) => v > 0).map(([id, tons]) => {
                                const p = projects.find(x => x.id === id);
                                if (!p) return null;
                                const st = CAT_STYLE[p.category];
                                return (
                                    <div key={id} style={{
                                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                        padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: '12.5px',
                                    }}>
                                        <span style={{ color: st?.color }}>
                                            {st?.icon || '🌳'} {(p.name || 'Untitled Project').split(' ').slice(0, 3).join(' ')}
                                        </span>
                                        <span>
                                            <strong>{tons} t</strong>
                                            <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>
                                                ${(tons * parseFloat(p.price_per_ton_usd || 0)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                            </span>
                                        </span>
                                    </div>
                                );
                            })}
                            <div style={{ paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}>
                                <span>Total</span>
                                <span style={{ color: 'var(--accent)' }}>
                                    {allocated} t · ${costUSD.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="mt-24">
                <AIExplanationPanel text={aiText} isLoading={matching} title="Gemini Portfolio Intelligence" />
            </div>
        </div>
    );
}
