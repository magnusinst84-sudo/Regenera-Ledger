const DEFAULT_EVENTS = [
    { date: '2024-01-15', title: 'Initial ESG Report Submitted', type: 'info', desc: 'Company submitted Q4 2023 ESG report for AI audit.' },
    { date: '2024-02-10', title: 'Greenwashing Flag Detected', type: 'danger', desc: 'Gemini AI flagged inconsistencies in Scope 2 emission claims.' },
    { date: '2024-03-01', title: 'Scope 3 Analysis Complete', type: 'success', desc: '14 tier-1 suppliers mapped. 3 high-risk suppliers identified.' },
    { date: '2024-04-05', title: 'Carbon Gap Report Generated', type: 'info', desc: '23% gap between reported and calculated emissions.' },
    { date: '2024-05-12', title: 'Farmer Credits Matched', type: 'success', desc: '12 farmers matched. 4,200 tCO₂ offset credits secured.' },
];

const TYPE_STYLES = {
    success: { dot: '#00f5a0', bg: 'rgba(0,245,160,0.08)', border: 'rgba(0,245,160,0.2)', icon: '✅' },
    danger: { dot: '#ff4d6d', bg: 'rgba(255,77,109,0.08)', border: 'rgba(255,77,109,0.2)', icon: '⚠️' },
    info: { dot: '#00d4ff', bg: 'rgba(0,212,255,0.08)', border: 'rgba(0,212,255,0.2)', icon: '📋' },
};

export default function AuditTimeline({ events = DEFAULT_EVENTS }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
            {events.map((ev, i) => {
                const s = TYPE_STYLES[ev.type] || TYPE_STYLES.info;
                return (
                    <div key={i} style={{ display: 'flex', gap: '16px' }}>
                        {/* Line + Dot */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div style={{
                                width: '12px', height: '12px', borderRadius: '50%',
                                background: s.dot, flexShrink: 0,
                                boxShadow: `0 0 8px ${s.dot}`,
                                marginTop: '4px',
                            }} />
                            {i < events.length - 1 && (
                                <div style={{ width: '2px', flex: 1, background: 'var(--border)', margin: '4px 0' }} />
                            )}
                        </div>

                        {/* Content */}
                        <div style={{
                            background: s.bg,
                            border: `1px solid ${s.border}`,
                            borderRadius: 'var(--radius-sm)',
                            padding: '12px 16px',
                            marginBottom: '12px',
                            flex: 1,
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                                <div style={{ fontWeight: 600, fontSize: '13.5px', color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span>{s.icon}</span> {ev.title}
                                </div>
                                <span style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{ev.date}</span>
                            </div>
                            {ev.desc && (
                                <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginTop: '5px' }}>{ev.desc}</p>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
