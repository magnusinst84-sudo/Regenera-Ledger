import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';

// Fix default marker icons for Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const farmerIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
});

const companyIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
});

// Category polygon colours
const POLYGON_COLORS = {
    'Forestry': '#4ade80',
    'Blue Carbon': '#00d4ff',
    'Regen-Ag': '#00f5a0',
    'DAC': '#a78bfa',
};

const DEFAULT_FARMERS = [
    { id: 1, name: 'Ravi Kumar', lat: 18.5, lng: 73.9, credits: 240, crop: 'Rice' },
    { id: 2, name: 'Priya Singh', lat: 17.4, lng: 78.5, credits: 180, crop: 'Wheat' },
    { id: 3, name: 'Anand Patel', lat: 23.0, lng: 72.6, credits: 310, crop: 'Cotton' },
    { id: 4, name: 'Sunita Devi', lat: 26.9, lng: 80.9, credits: 95, crop: 'Sugarcane' },
    { id: 5, name: 'Mohammed Ali', lat: 13.0, lng: 77.6, credits: 420, crop: 'Coffee' },
];

const DEFAULT_COMPANY = { name: 'Regenera Ledger Corp', lat: 20.5, lng: 78.9 };

function FlyTo({ center }) {
    const map = useMap();
    useEffect(() => { map.flyTo(center, 5); }, [center]);
    return null;
}

/**
 * ProjectMarkerOrPolygon
 * If the project has a `geo_polygon` array ([ [lat,lng], ... ]), renders a filled Leaflet Polygon.
 * Otherwise falls back to a simple Marker.
 */
function ProjectMarkerOrPolygon({ project, onSelect }) {
    const color = POLYGON_COLORS[project.category] || '#00f5a0';
    const popupContent = (
        <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', minWidth: '170px' }}>
            <strong style={{ color }}>{project.name}</strong><br />
            📍 {project.location}<br />
            Category: <strong>{project.category}</strong><br />
            Credits: <strong>{project.credits_available?.toLocaleString() || project.credits} tCO₂</strong><br />
            {project.price_per_ton_usd && <>Price: <strong>${project.price_per_ton_usd}/t</strong><br /></>}
            Credibility: <strong>★ {project.credibility_score || '—'}</strong>
        </div>
    );

    // ── Polygon mode (when backend provides boundary coordinates) ───
    if (Array.isArray(project.geo_polygon) && project.geo_polygon.length >= 3) {
        return (
            <Polygon
                positions={project.geo_polygon}   // [ [lat,lng], [lat,lng], … ]
                pathOptions={{
                    color,
                    fillColor: color,
                    fillOpacity: 0.2,
                    weight: 2,
                    dashArray: project.category === 'DAC' ? '6 4' : null,
                }}
                eventHandlers={{ click: () => onSelect?.(project) }}
            >
                <Popup>{popupContent}</Popup>
            </Polygon>
        );
    }

    // ── Fallback: simple Marker ──────────────────────────────────
    if (!project.lat || !project.lng) return null;
    return (
        <Marker
            position={[project.lat, project.lng]}
            icon={farmerIcon}
            eventHandlers={{ click: () => onSelect?.(project) }}
        >
            <Popup>{popupContent}</Popup>
        </Marker>
    );
}

export default function MapPicker({
    farmers = DEFAULT_FARMERS,
    company = DEFAULT_COMPANY,
    onSelect,
}) {
    return (
        <div style={{ width: '100%', height: '420px', borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid var(--border)' }}>
            <MapContainer
                center={[company.lat, company.lng]}
                zoom={4}
                style={{ height: '100%', width: '100%', background: '#0a0f1e' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {/* Company HQ marker */}
                <Marker position={[company.lat, company.lng]} icon={companyIcon}>
                    <Popup>
                        <strong>{company.name}</strong><br />
                        Company HQ
                    </Popup>
                </Marker>

                {/* Project markers OR polygons */}
                {farmers.map((f) => (
                    <ProjectMarkerOrPolygon
                        key={f.id}
                        project={f}
                        onSelect={onSelect}
                    />
                ))}
            </MapContainer>
        </div>
    );
}
