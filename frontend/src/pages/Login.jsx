import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [form, setForm] = useState({ email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await login(form);
            navigate('/dashboard');
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Invalid credentials. Please try again.'
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="auth-logo">
                    <h1>Regenera Ledger</h1>
                    <p>ESG Intelligence &amp; Carbon Transparency</p>
                </div>

                {error && (
                    <div style={{
                        background: 'rgba(255,77,109,0.12)', border: '1px solid rgba(255,77,109,0.3)',
                        borderRadius: '8px', padding: '10px 14px',
                        color: 'var(--danger)', fontSize: '13px', marginBottom: '16px',
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <input
                            id="email" type="email" className="form-input"
                            placeholder="you@company.com"
                            value={form.email}
                            onChange={(e) => setForm({ ...form, email: e.target.value })}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            id="password" type="password" className="form-input"
                            placeholder="••••••••"
                            value={form.password}
                            onChange={(e) => setForm({ ...form, password: e.target.value })}
                            required
                        />
                    </div>

                    <button
                        id="login-btn" type="submit"
                        className="btn btn-primary btn-lg w-full mt-8"
                        style={{ justifyContent: 'center' }}
                        disabled={loading}
                    >
                        {loading
                            ? <><div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px', margin: 0 }} /> Signing In...</>
                            : '🔐 Sign In'}
                    </button>
                </form>

                <div className="auth-link">
                    Don't have an account? <Link to="/register">Create one</Link>
                </div>
            </div>
        </div>
    );
}
