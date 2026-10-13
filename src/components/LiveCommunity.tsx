import React, { useCallback, useEffect, useState } from 'react';
import { CalendarDays, MapPin, Plus, TreePine, Users, Waves } from 'lucide-react';
import { savjApi, type ApiDrive } from '../data/apiClient';

type Props = { backendConnected: boolean; onNotice: (message: string) => void };
const formatDate = (value: string) => { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString(); };

export default function LiveCommunity({ backendConnected, onNotice }: Props) {
  const [drives, setDrives] = useState<ApiDrive[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [startsAt, setStartsAt] = useState('');
  const [capacity, setCapacity] = useState('');

  const load = useCallback(async () => {
    if (!backendConnected) return;
    setLoading(true);
    try { setDrives(await savjApi.listDrives()); }
    catch (error) { onNotice(error instanceof Error ? error.message : 'Could not load community drives.'); }
    finally { setLoading(false); }
  }, [backendConnected, onNotice]);
  useEffect(() => { void load(); }, [load]);

  const join = async (drive: ApiDrive) => {
    if (!backendConnected) { onNotice('Sign in from Settings to join a live community drive.'); return; }
    setBusyId(drive.id);
    try {
      const result = await savjApi.joinDrive(drive.id);
      await load();
      onNotice(result.status === 'already_joined' ? 'You have already joined this drive.' : 'You joined the community drive.');
    } catch (error) { onNotice(error instanceof Error ? error.message : 'Could not join this drive.'); }
    finally { setBusyId(null); }
  };

  const create = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!backendConnected) { onNotice('Sign in from Settings to publish a community drive.'); return; }
    const date = new Date(startsAt);
    if (Number.isNaN(date.getTime()) || date.getTime() <= Date.now()) { onNotice('Choose a future date and time.'); return; }
    setLoading(true);
    try {
      await savjApi.createDrive({ title: title.trim(), description: description.trim(), location_text: location.trim(), starts_at: date.toISOString(), capacity: capacity ? Number(capacity) : null });
      setTitle(''); setDescription(''); setLocation(''); setStartsAt(''); setCapacity(''); setShowForm(false);
      await load(); onNotice('Community drive published.');
    } catch (error) { onNotice(error instanceof Error ? error.message : 'Could not publish this drive.'); }
    finally { setLoading(false); }
  };

  return <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> MAKE CHANGE TOGETHER</div><h1>Community drives</h1><p className="subheading">Show up for your neighbourhood and the planet.</p></div><button className="primary-button" onClick={() => setShowForm((value) => !value)}><Plus size={17} /> Organise a drive</button></section>
    <div className="community-banner"><div><Users size={27} /><h2>Good work grows in good company.</h2><p>Join local cleanups, plantation events, and community-led environmental action.</p><small>{backendConnected ? 'Live community data' : 'Sign in to load live drives'}</small></div><div className="community-banner-art"><TreePine size={90} /><Waves size={45} /></div></div>
    {showForm && <form className="section-card" onSubmit={create} style={{ marginBottom: 20 }}><div className="section-heading"><div><h3>Organise a community drive</h3><p>Publish an event for neighbours to join.</p></div></div><label>Drive title<input required minLength={3} maxLength={120} value={title} onChange={(e) => setTitle(e.target.value)} /></label><label>Description<textarea maxLength={4000} value={description} onChange={(e) => setDescription(e.target.value)} rows={3} /></label><label>Location<input required minLength={2} maxLength={200} value={location} onChange={(e) => setLocation(e.target.value)} /></label><label>Date and time<input required type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} /></label><label>Participant limit (optional)<input type="number" min={1} max={100000} value={capacity} onChange={(e) => setCapacity(e.target.value)} /></label><button className="primary-button" type="submit" disabled={loading}>{loading ? 'Publishing…' : 'Publish drive'}</button></form>}
    {!backendConnected && <div className="demo-disclaimer">Open Settings and sign in to load live events, join them, or organise a new one.</div>}
    {loading && <p role="status">Loading community drives…</p>}
    {backendConnected && !loading && drives.length === 0 && <div className="section-card"><h3>No live drives yet</h3><p>Be the first to organise a community environmental drive.</p></div>}
    <div className="drive-cards">{drives.map((drive, i) => <article className="drive-card" key={drive.id}><div className={'drive-card-art art-' + (i % 2)}>{i % 2 === 0 ? <Waves size={44} /> : <TreePine size={44} />}<span>COMMUNITY ACTION</span></div><div className="drive-card-body"><span className="event-date"><CalendarDays size={14} /> {formatDate(drive.starts_at)}</span><h3>{drive.title}</h3><p><MapPin size={14} /> {drive.location_text}</p>{drive.description && <p>{drive.description}</p>}<div className="drive-card-footer"><span><Users size={15} /> {drive.participant_count}{drive.capacity ? ' / ' + drive.capacity : ''} joined</span><button className="primary-button" disabled={!backendConnected || busyId === drive.id || (drive.capacity !== null && drive.participant_count >= drive.capacity)} onClick={() => void join(drive)}>{busyId === drive.id ? 'Joining…' : 'Join drive'}</button></div></div></article>)}</div>
  </>;
}
