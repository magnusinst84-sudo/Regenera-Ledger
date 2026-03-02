import { useEffect, useRef } from 'react';

const DEFAULT_NODES = [
    { id: 'company', label: 'Your Company', type: 'company', x: 300, y: 200 },
    { id: 's1', label: 'Steel Corp', type: 'supplier', x: 120, y: 80 },
    { id: 's2', label: 'Logistics Ltd', type: 'supplier', x: 480, y: 80 },
    { id: 's3', label: 'Energy Co', type: 'supplier', x: 120, y: 320 },
    { id: 's4', label: 'Plastics Inc', type: 'supplier', x: 480, y: 320 },
    { id: 's5', label: 'Chemicals GmbH', type: 'tier2', x: 60, y: 200 },
    { id: 's6', label: 'Mining Group', type: 'tier2', x: 540, y: 200 },
];

const DEFAULT_EDGES = [
    { from: 'company', to: 's1', risk: 'high' },
    { from: 'company', to: 's2', risk: 'low' },
    { from: 'company', to: 's3', risk: 'medium' },
    { from: 'company', to: 's4', risk: 'high' },
    { from: 's1', to: 's5', risk: 'medium' },
    { from: 's2', to: 's6', risk: 'low' },
];

const RISK_COLOR = { high: '#ff4d6d', medium: '#ffd166', low: '#00f5a0' };
const NODE_COLOR = { company: '#00f5a0', supplier: '#00d4ff', tier2: '#a78bfa', disclosed: '#00d4ff', hidden: '#fbbf24' };

export default function NetworkGraph({ nodes = [], edges = [] }) {
    const svgRef = useRef(null);

    // Filter nodes to ensure we have a 'company' node if possible, or add it
    let cleanNodes = [...nodes];
    if (cleanNodes.length > 0 && !cleanNodes.find(n => n.id === 'Company')) {
        // Find if there's any 'company' type node
        const existingCompany = cleanNodes.find(n => n.type === 'company');
        if (!existingCompany) {
            // We'll treat the first node or a new node as Company center
        }
    }

    // Auto-layout: Assign x/y if missing
    const layoutNodes = cleanNodes.map((node, i) => {
        if (node.x !== undefined && node.y !== undefined) return node;

        // Root node at center
        if (node.id === 'Company' || node.type === 'company') {
            return { ...node, x: 300, y: 200 };
        }

        // Radial layout for others
        const angle = (i / (nodes.length - 1)) * Math.PI * 2;
        const radius = node.type === 'tier2' || node.type === 'hidden' ? 160 : 100;
        return {
            ...node,
            x: 300 + Math.cos(angle) * radius,
            y: 200 + Math.sin(angle) * radius
        };
    });

    const getNode = (id) => layoutNodes.find((n) => n.id === id);

    return (
        <div style={{ width: '100%', overflow: 'auto' }}>
            <svg
                ref={svgRef}
                viewBox="0 0 600 400"
                style={{ width: '100%', maxHeight: '420px', display: 'block', background: 'rgba(0,0,0,0.1)', borderRadius: '8px' }}
            >
                <defs>
                    <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                        <path d="M0,0 L0,6 L6,3 z" fill="rgba(255,255,255,0.3)" />
                    </marker>
                    {['high', 'medium', 'low'].map(r => (
                        <marker key={r} id={`arrow-${r}`} markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                            <path d="M0,0 L0,6 L6,3 z" fill={RISK_COLOR[r] || '#555'} />
                        </marker>
                    ))}
                </defs>

                {/* Edges */}
                {edges.map((e, i) => {
                    // Backend uses 'source' and 'target', old mock used 'from' and 'to'
                    const sourceId = e.source || e.from;
                    const targetId = e.target || e.to;
                    const from = getNode(sourceId);
                    const to = getNode(targetId);
                    if (!from || !to) return null;

                    return (
                        <line
                            key={i}
                            x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                            stroke={RISK_COLOR[e.risk] || '#555'}
                            strokeWidth="1.5"
                            strokeOpacity="0.6"
                            strokeDasharray={e.risk === 'high' ? '0' : '5,3'}
                            markerEnd={`url(#arrow-${e.risk || 'low'})`}
                        />
                    );
                })}

                {/* Nodes */}
                {layoutNodes.map((node) => (
                    <g key={node.id} transform={`translate(${node.x},${node.y})`}>
                        <circle
                            r={node.type === 'company' ? 28 : 20}
                            fill={`${NODE_COLOR[node.type] || '#ccc'}22`}
                            stroke={NODE_COLOR[node.type] || '#ccc'}
                            strokeWidth="1.5"
                        />
                        <text
                            textAnchor="middle"
                            dy="0.3em"
                            fontSize={node.type === 'company' ? 10 : 8}
                            fill={NODE_COLOR[node.type] || '#ccc'}
                            fontWeight="600"
                            fontFamily="Inter, sans-serif"
                        >
                            {node.label.length > 12 ? node.label.slice(0, 10) + '…' : node.label}
                        </text>
                    </g>
                ))}
            </svg>

            {/* Legend */}
            <div style={{ display: 'flex', gap: '16px', marginTop: '8px', flexWrap: 'wrap' }}>
                {Object.entries(RISK_COLOR).map(([risk, color]) => (
                    <div key={risk} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        <div style={{ width: '20px', height: '2px', background: color, borderRadius: '2px' }} />
                        {risk.charAt(0).toUpperCase() + risk.slice(1)} Risk
                    </div>
                ))}
                {Object.entries(NODE_COLOR).map(([type, color]) => (
                    <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', border: `2px solid ${color}`, background: `${color}22` }} />
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                    </div>
                ))}
            </div>
        </div>
    );
}
