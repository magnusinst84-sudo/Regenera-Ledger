import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import AuditTimeline from '../components/AuditTimeline';
import { getFarmerProfile, updateFarmerProfile } from '../api/api';

// Dynamic events generator helper
const getDynamicEvents = (profile) => {
    if (!profile.id) return [];
    const events = [];
    if (profile.created_at) {
        events.push({ date: profile.created_at.split('T')[0], title: 'Enrolled in Carbon Program', type: 'success', desc: 'Successfully joined the Regenera Ledger Carbon Marketplace.' });
    }
    if (profile.updated_at) {
        events.push({ date: profile.updated_at.split('T')[0], title: 'Profile Updated', type: 'info', desc: 'Profile details and land information updated.' });
    }
    if (profile.documents && profile.documents.length > 0) {
        events.push({ date: new Date().toISOString().split('T')[0], title: `${profile.documents.length} Document(s) Submitted`, type: 'info', desc: 'Verification documents uploaded for auditing.' });
    }
    return events.sort((a, b) => new Date(b.date) - new Date(a.date));
};

export default function FarmerProfile() {
    const [form, setForm] = useState({ name: '', email: '', phone: '', state: '', district: '', village: '', land_size: '', crops: '', practices: '' });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState('');
    const [showEstimatePrompt, setShowEstimatePrompt] = useState(false);

    useEffect(() => {
        getFarmerProfile()
            .then((res) => {
                if (res.data) setForm(res.data);
            })
            .catch(() => {
                // If no profile found, just keep the empty form
                console.log('No profile found for this user yet.');
            })
            .finally(() => setLoading(false));
    }, []);

    const upd = (k) => (e) => { setForm({ ...form, [k]: e.target.value }); setSaved(false); };


    const handleUploadMock = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const newDoc = { name: file.name, status: 'Uploaded', icon: '📄', date: new Date().toISOString() };
        setForm({ ...form, documents: [...(form.documents || []), newDoc] });
        setSaved(false);
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true); setError(''); setSaved(false); setShowEstimatePrompt(false);
        try {
            await updateFarmerProfile(form);
            setSaved(true);
            // Show estimate prompt after successful save
            if (form.land_size && form.crops) {
                setShowEstimatePrompt(true);
            }
        } catch {
            setError('Failed to save. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div>
                <div className="page-header">
                    <h1 className="page-title">Farmer Profile</h1>
                </div>
                <div className="grid-2">
                    <div className="card">
                        {[1, 2, 3, 4, 5].map(i => <div key={i} className="skeleton mb-16" style={{ height: '48px' }} />)}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Farmer Profile</h1>
                <p className="page-sub">Manage your land details, sustainable practices, and verification documents</p>
            </div>

            <div className="grid-2" style={{ alignItems: 'start' }}>
                {/* Form */}
                <div className="card">
                    <div className="card-title mb-16">Personal &amp; Farm Details</div>
                    <form onSubmit={handleSave}>
                        <div className="grid-2">
                            <div className="form-group">
                                <label className="form-label">Full Name</label>
                                <input className="form-input" value={form.name || ''} onChange={upd('name')} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Email</label>
                                <input className="form-input" type="email" value={form.email || ''} onChange={upd('email')} />
                            </div>
                        </div>
                        <div className="grid-2">
                            <div className="form-group">
                                <label className="form-label">Phone</label>
                                <input className="form-input" value={form.phone || ''} onChange={upd('phone')} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">State</label>
                                <input className="form-input" value={form.state || ''} onChange={upd('state')} />
                            </div>
                        </div>
                        <div className="grid-2">
                            <div className="form-group">
                                <label className="form-label">District</label>
                                <input className="form-input" value={form.district || ''} onChange={upd('district')} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Village</label>
                                <input className="form-input" value={form.village || ''} onChange={upd('village')} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Total Land Size (acres)</label>
                            <input className="form-input" type="number" value={form.land_size || ''} onChange={upd('land_size')} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Crops Grown</label>
                            <input className="form-input" value={form.crops || ''} onChange={upd('crops')} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Sustainable Practices</label>
                            <textarea className="form-textarea" value={form.practices || ''} onChange={upd('practices')} rows={3} />
                        </div>

                        {error && <p style={{ color: 'var(--danger)', fontSize: '13px', marginBottom: '10px' }}>{error}</p>}

                        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                            <button id="save-profile" type="submit" className="btn btn-primary" disabled={saving}>
                                {saving ? 'Saving...' : '💾 Save Profile'}
                            </button>
                            {saved && <span style={{ color: 'var(--accent)', fontSize: '13px' }}>✅ Saved successfully</span>}
                        </div>

                        {showEstimatePrompt && (
                            <div className="card mt-16" style={{ background: 'rgba(var(--accent-rgb), 0.1)', border: '1px solid var(--accent)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div>
                                        <div style={{ fontWeight: '600', color: 'var(--accent)', marginBottom: '4px' }}>Profile Complete!</div>
                                        <div style={{ fontSize: '13px' }}>Your land details are ready. Estimate your carbon credit potential now!</div>
                                    </div>
                                    {/* L3 FIX: Link to /farmer/estimate not /dashboard */}
                                    <Link to="/farmer/estimate" className="btn btn-primary btn-sm">
                                        Estimate Credits
                                    </Link>
                                </div>
                            </div>
                        )}
                    </form>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {/* Documents */}
                    <div className="card">
                        <div className="card-title mb-12">Verification Documents</div>
                        {(form.documents && form.documents.length > 0) ? (
                            <>
                                {form.documents.map((d, idx) => (
                                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                                        <span style={{ fontSize: '13.5px' }}>{d.icon || '📄'} {d.name}</span>
                                        <span className={`badge ${d.status === 'Verified' ? 'badge-green' : d.status === 'Uploaded' ? 'badge-blue' : 'badge-yellow'}`}>{d.status}</span>
                                    </div>
                                ))}
                            </>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-muted)', fontSize: '13px' }}>
                                {form.id ? 'No documents found for this profile.' : 'Please add required documents before verification.'}
                            </div>
                        )}
                        <label className="btn btn-secondary btn-sm mt-16" style={{ cursor: 'pointer', display: 'inline-flex' }}>
                            📁 Upload Document
                            <input type="file" style={{ display: 'none' }} onChange={handleUploadMock} />
                        </label>
                    </div>

                    {/* Timeline */}
                    <div className="card">
                        <div className="card-title mb-16">Activity Timeline</div>
                        {form.id ? (
                            <AuditTimeline events={getDynamicEvents(form)} />
                        ) : (
                            <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No activity yet. Complete your profile to start your journey.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
