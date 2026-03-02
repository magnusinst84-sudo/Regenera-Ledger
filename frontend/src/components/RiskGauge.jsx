import { Doughnut } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function RiskGauge({ score = 72, label = 'ESG Score' }) {
    const getColor = (s) => {
        if (s >= 70) return ['#00f5a0', '#00d4ff'];
        if (s >= 40) return ['#ffd166', '#f4a261'];
        return ['#ff4d6d', '#c9184a'];
    };

    const [c1, c2] = getColor(score);

    const data = {
        datasets: [
            {
                data: [score, 100 - score],
                backgroundColor: [c1, 'rgba(255,255,255,0.05)'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '75%',
        plugins: {
            legend: { display: false },
            tooltip: { enabled: false },
        },
        animation: { duration: 800, easing: 'easeInOutQuart' },
    };

    return (
        <div style={{ textAlign: 'center', position: 'relative', height: '160px' }}>
            <Doughnut data={data} options={options} style={{ height: '140px' }} />
            <div style={{
                position: 'absolute', bottom: '12px', left: '50%',
                transform: 'translateX(-50%)',
                display: 'flex', flexDirection: 'column', alignItems: 'center',
            }}>
                <span style={{ fontSize: '32px', fontWeight: 800, color: c1, lineHeight: 1 }}>
                    {score}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {label}
                </span>
            </div>
        </div>
    );
}
