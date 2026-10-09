import React, { useEffect } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export type MapTask = {
  id: number; title: string; location: string; category: string; budget: number;
  latitude?: number | null; longitude?: number | null; distance: number;
};
type Coordinates = { latitude: number; longitude: number } | null;

function Recenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => { map.setView(center, map.getZoom()); }, [map, center[0], center[1]]);
  return null;
}

export default function InteractiveMap({ tasks, origin, onSelect }: { tasks: MapTask[]; origin: Coordinates; onSelect: (task: MapTask) => void }) {
  const center: [number, number] = origin ? [origin.latitude, origin.longitude] : [18.5204, 73.8567];
  const mappedTasks = tasks.filter((task) => task.latitude != null && task.longitude != null);
  return <div className="map-panel"><div className="map-header"><strong>Task map</strong><span>{origin ? 'Centered on your location' : 'Pune preview · enable location to recenter'}</span></div>
    <MapContainer center={center} zoom={12} scrollWheelZoom style={{ height: 420, width: '100%', borderRadius: 12, zIndex: 0 }}>
      <Recenter center={center}/>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
      {origin && <CircleMarker center={center} radius={9} pathOptions={{ color: '#1f5b43', fillColor: '#5ca879', fillOpacity: 0.9 }}><Popup>Your current location (kept in this browser session).</Popup></CircleMarker>}
      {mappedTasks.map((task) => <CircleMarker key={task.id} center={[task.latitude as number, task.longitude as number]} radius={8} pathOptions={{ color: '#245e43', fillColor: '#7cb98b', fillOpacity: 0.85 }}><Popup><strong>{task.title}</strong><br/>{task.location}<br/>{task.category}<br/>{task.distance.toFixed(1)} km away<br/><strong>₹{task.budget.toLocaleString('en-IN')}</strong><br/><button type="button" onClick={() => onSelect(task)}>View task</button></Popup></CircleMarker>)}
    </MapContainer>
    <p className="map-note">{mappedTasks.length} task{mappedTasks.length === 1 ? '' : 's'} have coordinates and are shown. {tasks.length - mappedTasks.length} task{tasks.length - mappedTasks.length === 1 ? '' : 's'} without coordinates cannot be pinned. Map tiles are provided by OpenStreetMap for this prototype; production traffic needs a compliant tile-provider plan.</p>
  </div>;
}
