import { Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Tooltip,
    Legend,
} from 'chart.js';
import AIExplanationPanel from '../components/AIExplanationPanel';
import { useState } from 'react';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend);

const YEARS = ['2020', '2021', '2022', '2023', '2024'];
const REPORTED = [14200, 13800, 12900, 12400, 11800];
const TARGET = [14000, 12600, 11200, 9800, 8400];
const CALCULATED = [14800, 14500, 15100, 14200, 13600];

const MOCK_AI = `Carbon Gap Analysis — Gemini Insights:

The gap between your reported emissions (11,800 tCO₂) and independently calculated emissions (13,600 tCO₂) represents a 15.3% discrepancy in 2024. This is the widest gap in the 5-year dataset.

Key Findings:
• Your net-zero target trajectory requires a 16.7% annual reduction. Current performance shows only 4.5% YoY reduction.
• At the current rate, net-zero will be achieved by 2047, not 2035 as stated.
• The divergence between reported and calculated figures suggests possible incomplete boundary definitions.

Recommended Actions:
1. Commission third-party verification for 2023-2024 data
2. Extend emission boundary to include Scope 3 Category 11 (use of sold products)
3. Consider purchasing 1,800 tCO₂ offsets to bridge the current year gap`;

export default function CarbonGap() {
    const [aiText, setAiText] = useState('');
    const [loading, setLoading] = useState(false);

    const handleAnalyze = async () => {
        setLoading(true); setAiText('');
        await new Promise((r) => setTimeout(r, 1200));
        setAiText(MOCK_AI);
        setLoading(false);
    };

    const chartData = {
        labels: YEARS,
        datasets: [
            {
                label: 'Reported (tCO₂)',
                data: REPORTED,
                backgroundColor: 'rgba(0,245,160,0.25)',
                borderColor: '#00f5a0',
                borderWidth: 2,
                borderRadius: 6,
                type: 'bar',
            },
            {
                label: 'Calculated (tCO₂)',
                data: CALCULATED,
                backgroundColor: 'rgba(255,77,109,0.2)',
                borderColor: '#ff4d6d',
                borderWidth: 2,
                borderRadius: 6,
                type: 'bar',
            },
            {
                label: 'Target (tCO₂)',
                data: TARGET,
                type: 'line',
                borderColor: '#00d4ff',
                borderWidth: 2,
                borderDash: [6, 4],
                pointBackgroundColor: '#00d4ff',
                tension: 0.4,
                fill: false,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: '#b0bec5', font: { family: 'Inter', size: 12 } },
            },
            tooltip: { mode: 'index', intersect: false },
        },
        scales: {
            x: { ticks: { color: '#7a8aaa' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: {
                ticks: { color: '#7a8aaa', callback: (v) => `${(v / 1000).toFixed(0)}k` },
                grid: { color: 'rgba(255,255,255,0.05)' },
            },
        },
    };

    const gap2024 = CALCULATED[4] - REPORTED[4];
    const gapPct = ((gap2024 / CALCULATED[4]) * 100).toFixed(1);

    return (
        <div>
            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Carbon Gap Analysis</h1>
                    <p className="page-sub">Compare reported vs. calculated emissions against net-zero targets</p>
                </div>
                <button id="gap-analyze" className="btn btn-primary" onClick={handleAnalyze} disabled={loading}>
                    {loading ? '⏳ Calculating...' : '📉 Run Gap Analysis'}
                </button>
            </div>

            <div className="stats-grid mb-24">
                {[
                    { icon: '📊', value: '11,800', label: 'Reported tCO₂ (2024)', color: 'var(--accent)' },
                    { icon: '🔢', value: '13,600', label: 'Calculated tCO₂ (2024)', color: 'var(--danger)' },
                    { icon: '⬆️', value: `${gap2024}`, label: 'Emission Gap (tCO₂)', color: 'var(--warning)' },
                    { icon: '📏', value: `${gapPct}%`, label: 'Gap Percentage', color: 'var(--warning)' },
                ].map((s) => (
                    <div className="stat-card" key={s.label}>
                        <span className="stat-icon">{s.icon}</span>
                        <span className="stat-value" style={{ color: s.color }}>{s.value}</span>
                        <span className="stat-label">{s.label}</span>
                    </div>
                ))}
            </div>

            <div className="card mb-24">
                <div className="card-title mb-16">Emissions Over Time</div>
                <div style={{ height: '320px', position: 'relative' }}>
                    <Bar data={chartData} options={chartOptions} />
                </div>
            </div>

            <AIExplanationPanel text={aiText} isLoading={loading} title="Gemini Carbon Gap Insights" />
        </div>
    );
}
