/**
 * OffsetProjectCard.jsx
 * Renders a distinctly themed card based on project.category.
 * Supports: 'Blue Carbon' | 'DAC' | 'Tech-Based DAC' | 'Forestry' | 'Regen-Ag'
 *
 * Props:
 *   project  — { id, name, location, category,
 *                financials: { price_per_ton_usd },
 *                metrics:    { durability_years, available_inventory_tons, co_benefits[] },
 *                credibility_score }
 *   ons     — current allocated tons (controlled from parent)
 *   onAdd    — fn(projectId, tons)
 *   onDelete — fn(projectId)
 *   selected — boolean (card is in the active portfolio)
 */
import { useState } from 'react';

// ── Per-category theme config ─────────────────────────────────────
const THEMES = {
    'Blue Carbon': {
        icon: '🌊', label: 'Blue Carbon',
        accent: '#00d4ff', accentSoft: 'rgba(0,212,255,0.13)',
        border: 'rgba(0,212,255,0.42)', borderActive: '#00d4ff',
        glow: '0 0 24px rgba(0,212,255,0.3)',
        badgeBg: 'rgba(0,212,255,0.11)', badgeBorder: 'rgba(0,212,255,0.35)',
    },
    'DAC': {
        icon: '⚗️', label: 'Tech-Based DAC',
        accent: '#a78bfa', accentSoft: 'rgba(167,139,250,0.12)',
        border: 'rgba(167,139,250,0.38)', borderActive: '#a78bfa',
        glow: '0 0 24px rgba(167,139,250,0.28)',
        badgeBg: 'rgba(167,139,250,0.11)', badgeBorder: 'rgba(167,139,250,0.35)',
    },
    'Tech-Based DAC': {
        icon: '⚗️', label: 'Tech-Based DAC',
        accent: '#a78bfa', accentSoft: 'rgba(167,139,250,0.12)',
        border: 'rgba(167,139,250,0.38)', borderActive: '#a78bfa',
        glow: '0 0 24px rgba(167,139,250,0.28)',
        badgeBg: 'rgba(167,139,250,0.11)', badgeBorder: 'rgba(167,139,250,0.35)',
    },
    'Forestry': {
        icon: '🌲', label: 'Forestry',
        accent: '#4ade80', accentSoft: 'rgba(74,222,128,0.1)',
        border: 'rgba(74,222,128,0.36)', borderActive: '#4ade80',
        glow: '0 0 24px rgba(74,222,128,0.22)',
        badgeBg: 'rgba(74,222,128,0.1)', badgeBorder: 'rgba(74,222,128,0.3)',
    },
    'Regen-Ag': {
        icon: '🌾', label: 'Regen-Ag',
        accent: '#00f5a0', accentSoft: 'rgba(0,245,160,0.1)',
        border: 'rgba(0,245,160,0.36)', borderActive: '#00f5a0',
        glow: '0 0 22px rgba(0,245,160,0.2)',
        badgeBg: 'rgba(0,245,160,0.09)', badgeBorder: 'rgba(0,245,160,0.3)',
    },
};

// ── Category-specific metric sections ─────────────────────────────

/** Blue Carbon: Biodiversity Badges for each co-benefit */
function BiodiversityBadges({ coBenefits, theme }) {
    const benefits = coBenefits?.length
        ? coBenefits
        : ['Marine Protection', 'Storm Surge Mitigation', 'Biodiversity Hotspot', 'Fishery Restoration'];
    return (
        <div style={{ marginTop: '12px' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '7px' }}>
                🐠 Marine Co-Benefits
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {benefits.map(b => (
                    <span key={b} style={{
                        fontSize: '10.5px', fontWeight: 600, padding: '4px 11px', borderRadius: '99px',
                        background: theme.badgeBg, color: theme.accent, border: `1px solid ${theme.badgeBorder}`,
                        whiteSpace: 'nowrap',
                    }}>
                        {b}
                    </span>
                ))}
            </div>
        </div>
    );
}

/** DAC: Giant permanence number — the core selling point */
function DurabilityBlock({ years, theme }) {
    const display = years >= 999 ? '∞ Permanent' : `${years.toLocaleString()} Yrs`;
    return (
        <div style={{
            marginTop: '14px', padding: '16px', borderRadius: '12px', textAlign: 'center',
            background: 'rgba(0,0,0,0.3)', border: `1px solid ${theme.border}`,
        }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '6px', fontWeight: 600 }}>
                ⛓ Carbon Durability
            </div>
            <div style={{ fontSize: '36px', fontWeight: 900, color: theme.accent, lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>
                {display}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Geologically stored · IPCC Tier 1 certified
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
                {['MRV Monitored', 'ISO 14064', 'Gold Standard'].map(b => (
                    <span key={b} style={{
                        fontSize: '10px', fontWeight: 600, padding: '3px 10px', borderRadius: '99px',
                        background: theme.badgeBg, color: theme.accent, border: `1px solid ${theme.badgeBorder}`,
                    }}>
                        {b}
                    </span>
                ))}
            </div>
        </div>
    );
}

/** Forestry: Bold inventory scale bar for enterprise buyers */
function InventoryBar({ tons, theme }) {
    const MAX = 20000;
    const pct = Math.min(100, Math.round((tons / MAX) * 100));
    const label = tons >= 10000 ? `${(tons / 1000).toFixed(0)}K+ Tons Available` : `${tons?.toLocaleString() || 0} Tons Available`;
    return (
        <div style={{ marginTop: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                    🌳 Inventory Scale
                </span>
                <span style={{ fontSize: '16px', fontWeight: 800, color: theme.accent }}>{label}</span>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '99px', height: '7px', overflow: 'hidden' }}>
                <div style={{
                    width: `${pct}%`, height: '7px', borderRadius: '99px',
                    background: `linear-gradient(90deg, ${theme.accent}, ${theme.accent}99)`,
                    transition: 'width 0.6s ease',
                }} />
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '5px' }}>
                Enterprise-grade supply · suitable for deficits up to {MAX.toLocaleString()} tCO₂
            </div>
        </div>
    );
}

/** Regen-Ag: Social impact co-benefits for smallholder farmers */
function FarmerImpactBlock({ coBenefits, theme }) {
    const benefits = coBenefits?.length
        ? coBenefits
        : ['Farmer Income Uplift', 'Soil Health Improvement', 'Water Conservation', 'Rural Employment'];
    return (
        <div style={{ marginTop: '12px' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '7px' }}>
                🤝 Social Co-Benefits
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {benefits.map(b => (
                    <span key={b} style={{
                        fontSize: '10.5px', fontWeight: 600, padding: '4px 11px', borderRadius: '99px',
                        background: theme.badgeBg, color: theme.accent, border: `1px solid ${theme.badgeBorder}`,
                        whiteSpace: 'nowrap',
                    }}>
                        {b}
                    </span>
                ))}
            </div>
        </div>
    );
}

// ── Main component ────────────────────────────────────────────────
export default function OffsetProjectCard({ project, tons = 0, onAdd, onDelete, selected = false }) {
    const cat = project.category || 'Forestry';
    const theme = THEMES[cat] || THEMES['Forestry'];
    const price = parseFloat(project.financials?.price_per_ton_usd ?? project.price_per_ton_usd ?? 0);
    const inventory = project.metrics?.available_inventory_tons ?? project.credits_available ?? 0;
    // M3 FIX: safely parse durability — '∞ Permanent' string → 999 so DurabilityBlock shows ∞
    const rawDurability = project.metrics?.durability_years ?? project.durability_years ?? 30;
    const durability = (typeof rawDurability === 'string' && (rawDurability.includes('∞') || rawDurability.toLowerCase().includes('perm')))
        ? 999
        : (parseFloat(rawDurability) || 30);
    const coBenefits = project.metrics?.co_benefits ?? [];
    const credibility = project.credibility_score ?? 75;
    const projectLead = project.owner_name || project.name;
    const contactEmail = project.email || 'contact@carbon-india.org';

    const [inputTons, setInputTons] = useState(tons);
    const lineCost = Math.round(inputTons * price);

    // Category-specific metrics rendered via switch
    const renderCategoryMetrics = () => {
        switch (cat) {
            case 'Blue Carbon':
                return <BiodiversityBadges coBenefits={coBenefits} theme={theme} />;
            case 'DAC':
            case 'Tech-Based DAC':
                return <DurabilityBlock years={durability} theme={theme} />;
            case 'Forestry':
                return <InventoryBar tons={inventory} theme={theme} />;
            case 'Regen-Ag':
                return <FarmerImpactBlock coBenefits={coBenefits} theme={theme} />;
            default:
                return null;
        }
    };

    return (
        <div style={{
            borderRadius: '16px', padding: '20px',
            background: selected ? theme.accentSoft : 'var(--surface)',
            border: `${selected ? '2px' : '1px'} solid ${selected ? theme.borderActive : theme.border}`,
            boxShadow: selected ? theme.glow : 'none',
            transition: 'all 0.25s ease',
            display: 'flex', flexDirection: 'column',
        }}>

            {/* ── Header row ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                    <span style={{
                        display: 'inline-block', marginBottom: '7px',
                        fontSize: '10px', fontWeight: 700, padding: '3px 11px', borderRadius: '20px',
                        background: theme.badgeBg, color: theme.accent,
                        border: `1px solid ${theme.badgeBorder}`,
                        textTransform: 'uppercase', letterSpacing: '0.08em',
                    }}>
                        {theme.icon} {theme.label}
                    </span>
                    <div style={{ fontSize: '14.5px', fontWeight: 700, lineHeight: 1.35, marginBottom: '3px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        {project.name}
                        {onDelete && (
                            <button
                                onClick={(e) => { e.stopPropagation(); if (window.confirm('Remove this farmer profile?')) onDelete(project.id); }}
                                style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '14px', opacity: 0.6 }}
                                title="Delete Profile"
                            >
                                🗑️
                            </button>
                        )}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        👤 Project Lead: <strong style={{ color: 'var(--text)' }}>{projectLead}</strong> · 📍 {project.location}
                        {durability >= 999
                            ? ' · ♾️ Permanent'
                            : ` · ${durability}-yr durability`}
                    </div>
                </div>

                {/* Price box */}
                <div style={{
                    textAlign: 'right', flexShrink: 0, marginLeft: '14px',
                    padding: '10px 14px', borderRadius: '12px',
                    background: 'rgba(0,0,0,0.22)', border: `1px solid ${theme.border}`,
                }}>
                    <div style={{ fontSize: '22px', fontWeight: 900, color: theme.accent, lineHeight: 1 }}>
                        ${price.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>per tCO₂</div>
                    <div style={{ marginTop: '6px' }}>
                        <span style={{
                            padding: '2px 8px', borderRadius: '99px', fontSize: '10px', fontWeight: 700,
                            background: credibility === 'Audit Pending' ? 'rgba(255,165,0,0.12)' : (credibility >= 90 ? 'rgba(0,245,160,0.12)' : 'rgba(0,212,255,0.12)'),
                            color: credibility === 'Audit Pending' ? '#ffa500' : (credibility >= 90 ? '#00f5a0' : '#00d4ff'),
                        }}>
                            {typeof credibility === 'number' ? `★ ${credibility}` : credibility}
                        </span>
                    </div>
                </div>
            </div>

            {/* ── Category-specific metrics ── */}
            {renderCategoryMetrics()}

            {/* ── Allocation control ── */}
            <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    <span>Allocate tons (max: {inventory.toLocaleString()} t available)</span>
                    {inputTons > 0 && (
                        <span style={{ color: theme.accent, fontWeight: 700 }}>
                            ${lineCost.toLocaleString()} est.
                        </span>
                    )}
                </div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '12px' }}>
                    <input
                        type="range" min="0"
                        max={Math.min(inventory, 2000)} step="10"
                        value={inputTons}
                        onChange={e => setInputTons(Number(e.target.value))}
                        style={{ flex: 1, accentColor: theme.accent }}
                    />
                    <input
                        type="number" min="0" max={inventory} value={inputTons}
                        onChange={e => setInputTons(Math.max(0, Math.min(Number(e.target.value), inventory)))}
                        style={{
                            width: '74px', padding: '6px 8px', textAlign: 'center',
                            fontSize: '12px', fontWeight: 600,
                            background: 'rgba(255,255,255,0.06)',
                            border: `1px solid ${inputTons > 0 ? theme.accent : 'var(--border)'}`,
                            borderRadius: '7px', color: 'var(--text)',
                        }}
                    />
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>t</span>
                </div>

                {/* Add to Portfolio button */}
                <button
                    id={`add-${project.id}`}
                    onClick={() => onAdd?.(project.id, inputTons)}
                    disabled={inputTons === 0}
                    style={{
                        width: '100%', padding: '11px', borderRadius: '10px',
                        fontWeight: 700, fontSize: '13px',
                        cursor: inputTons === 0 ? 'not-allowed' : 'pointer',
                        border: `1.5px solid ${inputTons > 0 ? theme.accent : 'var(--border)'}`,
                        background: inputTons > 0 ? theme.accentSoft : 'transparent',
                        color: inputTons > 0 ? theme.accent : 'var(--text-muted)',
                        transition: 'all 0.2s',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                    }}
                >
                    {inputTons > 0
                        ? <>{theme.icon} Add {inputTons.toLocaleString()} t to Portfolio · ${lineCost.toLocaleString()}</>
                        : 'Set allocation to add to portfolio'}
                </button>
                <button
                    onClick={() => window.location.href = `mailto:${contactEmail}`}
                    style={{
                        width: '100%', marginTop: '8px', padding: '8px', borderRadius: '8px',
                        fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)',
                        background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)',
                        cursor: 'pointer', transition: 'all 0.2s',
                    }}
                    onMouseOver={e => e.currentTarget.style.color = theme.accent}
                    onMouseOut={e => e.currentTarget.style.color = 'var(--text-muted)'}
                >
                    ✉️ Contact {projectLead.split(' ')[0]}
                </button>
            </div>
        </div>
    );
}
