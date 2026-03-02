import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ROLES = ['Company / Corporate', 'Farmer / Agricultural Producer', 'ESG Analyst', 'Auditor'];
const SECTORS = ['Manufacturing', 'Logistics', 'Tech', 'Agriculture'];
const SECTOR_ICONS = { Manufacturing: '🏭', Logistics: '🚛', Tech: '💻', Agriculture: '🌾' };

export default function Register() {
    const navigate = useNavigate();
    const { register } = useAuth();
    const [form, setForm] = useState({ name: '', email: '', password: '', role: ROLES[0], sector: SECTORS[0] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const upd = (k) => (e) => setForm({ ...form, [k]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            // Map descriptive UI roles to short backend keys
            const roleMapping = {
                'Company / Corporate': 'company',
                'Farmer / Agricultural Producer': 'farmer',
                'ESG Analyst': 'company', // Treat as company for now
                'Auditor': 'company'      // Treat as auditor for now
            };

            const submitData = {
                ...form,
                role: roleMapping[form.role] || 'company'
            };

            await register(submitData);
            navigate('/login');
        } catch (err) {
            console.error('Registration error:', err);
            const msg = err.response?.data?.detail || 'Registration failed. Please make sure your backend is running and you have filled the .env file.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card" style={{ maxWidth: '460px' }}>
                <div className="auth-logo">
                    <h1>Create Account</h1>
                    <p>Join the ESG transparency movement</p>
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
                        <label className="form-label">Full Name</label>
                        <input id="reg-name" type="text" className="form-input" placeholder="Arjun Sharma" value={form.name} onChange={upd('name')} required />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <input id="reg-email" type="email" className="form-input" placeholder="you@company.com" value={form.email} onChange={upd('email')} required />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input id="reg-password" type="password" className="form-input" placeholder="Min. 8 characters" value={form.password} onChange={upd('password')} required minLength={8} />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Role</label>
                        <select id="reg-role" className="form-select" value={form.role} onChange={upd('role')}>
                            {ROLES.map((r) => <option key={r}>{r}</option>)}
                        </select>
                    </div>

                    {/* Industry sector — only for Company accounts */}
                    {form.role === 'Company / Corporate' && (
                        <div className="form-group">
                            <label className="form-label">
                                Industry Sector
                                <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: '6px', fontSize: '11px' }}>
                                    — determines which GHG Protocol rules Gemini applies
                                </span>
                            </label>
                            <select id="reg-sector" className="form-select" value={form.sector} onChange={upd('sector')}>
                                {SECTORS.map(s => (
                                    <option key={s} value={s}>{SECTOR_ICONS[s]} {s}</option>
                                ))}
                            </select>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', paddingLeft: '2px' }}>
                                {{
                                    Manufacturing: '🏭 GHG Protocol — Scope 1 + 2 from machines, Scope 3 upstream materials',
                                    Logistics: '🚛 GHG Protocol — Scope 1 diesel fleet, Scope 3 freight emission factors',
                                    Tech: '💻 GHG Protocol — Scope 2 data centre PUE, Scope 3 hardware lifecycle',
                                    Agriculture: '🌾 GHG Protocol — Scope 1 enteric fermentation, Scope 3 land use change',
                                }[form.sector]}
                            </div>
                        </div>
                    )}

                    <button id="register-btn" type="submit" className="btn btn-primary btn-lg w-full mt-8" style={{ justifyContent: 'center' }} disabled={loading}>
                        {loading ? 'Creating Account...' : '🚀 Get Started'}
                    </button>
                </form>

                <div className="auth-link">
                    Already have an account? <Link to="/login">Sign in</Link>
                </div>
            </div>
        </div>
    );
}
