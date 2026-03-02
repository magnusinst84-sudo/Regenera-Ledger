import { useEffect, useRef, useState } from 'react';

export default function AIExplanationPanel({ text, isLoading, title = 'Gemini AI Analysis' }) {
    const [displayed, setDisplayed] = useState('');
    const intervalRef = useRef(null);

    // Typewriter animation when text changes
    useEffect(() => {
        if (!text) { setDisplayed(''); return; }
        setDisplayed('');
        let i = 0;
        clearInterval(intervalRef.current);
        intervalRef.current = setInterval(() => {
            i++;
            setDisplayed(text.slice(0, i));
            if (i >= text.length) clearInterval(intervalRef.current);
        }, 12);
        return () => clearInterval(intervalRef.current);
    }, [text]);

    return (
        <div style={{
            background: 'rgba(0,245,160,0.04)',
            border: '1px solid rgba(0,245,160,0.18)',
            borderRadius: 'var(--radius)',
            padding: '20px',
            position: 'relative',
            overflow: 'hidden',
        }}>
            {/* Glow blob */}
            <div style={{
                position: 'absolute', top: '-40px', right: '-40px',
                width: '120px', height: '120px',
                background: 'radial-gradient(circle, rgba(0,245,160,0.12) 0%, transparent 70%)',
                borderRadius: '50%', pointerEvents: 'none',
            }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                <span style={{ fontSize: '20px' }}>🤖</span>
                <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--accent)' }}>{title}</span>
                {isLoading && (
                    <div style={{
                        marginLeft: 'auto', display: 'flex', gap: '4px', alignItems: 'center'
                    }}>
                        {[0, 1, 2].map(i => (
                            <div key={i} style={{
                                width: '6px', height: '6px', borderRadius: '50%',
                                background: 'var(--accent)',
                                animation: `bounce 1.2s ${i * 0.2}s ease-in-out infinite`,
                            }} />
                        ))}
                    </div>
                )}
            </div>

            {isLoading && !text ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {[80, 65, 90, 55].map((w, i) => (
                        <div key={i} className="skeleton" style={{ height: '14px', width: `${w}%` }} />
                    ))}
                </div>
            ) : text ? (
                <p style={{ fontSize: '13.5px', lineHeight: '1.8', color: 'var(--text-2)', whiteSpace: 'pre-wrap' }}>
                    {displayed}
                    {displayed.length < (text?.length || 0) && (
                        <span style={{ borderRight: '2px solid var(--accent)', marginLeft: '1px', animation: 'blink 0.7s step-end infinite' }} />
                    )}
                </p>
            ) : (
                <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    Upload a document or run analysis to see AI insights here...
                </p>
            )}

            <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
        @keyframes blink {
          50% { opacity: 0; }
        }
      `}</style>
        </div>
    );
}
