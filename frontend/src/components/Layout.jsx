import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV = [
    { section: 'Company', role: 'company' },
    { to: '/dashboard', icon: '📊', label: 'Dashboard', role: 'company' },
    { to: '/esg-analysis', icon: '🔬', label: 'ESG Analysis', role: 'company' },
    { to: '/scope3', icon: '🌐', label: 'Scope 3 Map', role: 'company' },
    { to: '/carbon-gap', icon: '📉', label: 'Carbon Gap', role: 'company' },
    { to: '/matching', icon: '🗺️', label: 'Farmer Match', role: 'company' },

    { section: 'Farmer', role: 'farmer' },
    { to: '/dashboard', icon: '🌾', label: 'Dashboard', role: 'farmer' },
    { to: '/farmer/profile', icon: '👤', label: 'Profile', role: 'farmer' },
    { to: '/farmer/estimate', icon: '💰', label: 'Estimation', role: 'farmer' },
];

export default function Layout() {
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    // Filter nav items based on user role
    const filteredNav = NAV.filter(item => !item.role || item.role === user?.role);

    const initials = user?.name
        ? user.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
        : 'RL';

    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <div className="logo-text">Regenera Ledger</div>
                </div>

                <nav className="sidebar-nav" style={{ marginTop: '16px' }}>
                    {filteredNav.map((item, i) =>
                        item.section ? (
                            <div key={i} className="sidebar-section">{item.section}</div>
                        ) : (
                            <NavLink
                                key={item.to}
                                to={item.to}
                                end={item.to === '/farmer' || item.to === '/dashboard'}
                                className={({ isActive }) =>
                                    'sidebar-link' + (isActive ? ' active' : '')
                                }
                            >
                                <span className="nav-icon">{item.icon}</span>
                                {item.label}
                            </NavLink>
                        )
                    )}
                </nav>

                <div className="sidebar-bottom">
                    <div className="user-chip">
                        <div className="user-avatar">{initials}</div>
                        <div className="user-info">
                            <div className="user-name">{user?.name || 'User'}</div>
                            <div className="user-role" style={{ textTransform: 'capitalize' }}>{user?.role || 'Guest'}</div>
                        </div>
                    </div>
                    <button
                        className="btn btn-secondary btn-sm w-full mt-8"
                        style={{ justifyContent: 'center' }}
                        onClick={() => { logout(); navigate('/login'); }}
                    >
                        Sign Out
                    </button>
                </div>
            </aside>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
}
