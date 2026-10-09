import React, { useEffect, useState } from 'react';
import { MapPin, Search, ShieldCheck, Users } from 'lucide-react';
import { savjApi, type ApiWorker } from '../data/apiClient';

export default function WorkerDirectory({ backendConnected, onNotice, onExplore }: { backendConnected: boolean; onNotice: (message: string) => void; onExplore: () => void }) {
  const [workers, setWorkers] = useState<ApiWorker[]>([]);
  const [search, setSearch] = useState('');
  const [skill, setSkill] = useState('');
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!backendConnected) return;
    let cancelled = false;
    setLoading(true);
    void savjApi.listWorkers(search, skill).then((items) => { if (!cancelled) setWorkers(items); })
      .catch((error) => { if (!cancelled) onNotice(error instanceof Error ? error.message : 'Could not load worker profiles.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [backendConnected, search, skill, onNotice]);
  return <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> SKILLS IN YOUR COMMUNITY</div><h1>Find local helpers</h1><p className="subheading">Discover worker profiles and skills shared by SAVJ members.</p></div></section>
    <div className="explore-toolbar"><div className="search-box"><Search size={17}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name or locality" aria-label="Search workers"/></div><div className="filter-control"><select value={skill} onChange={(e) => setSkill(e.target.value)} aria-label="Filter by skill"><option value="">All skills</option><option>Cleanup</option><option>Gardening</option><option>Plantation</option><option>Waste sorting</option><option>General helper</option><option>Cooking</option><option>Packing</option></select></div></div>
    {!backendConnected && <div className="demo-disclaimer">Sign in from Settings to discover live worker profiles. No sample workers are presented as real accounts.</div>}
    {loading && <p role="status">Loading worker profiles…</p>}
    {backendConnected && !loading && workers.length === 0 && <div className="section-card"><Users size={26}/><h3>No matching worker profiles yet</h3><p>Try a different skill or locality search.</p></div>}
    <div className="content-grid">{workers.map((worker) => <article className="section-card" key={worker.id}><div className="section-heading"><div><h3>{worker.display_name}</h3><p><MapPin size={14}/> {worker.locality}</p></div><span className="avatar">{worker.display_name.slice(0,2).toUpperCase()}</span></div><p><ShieldCheck size={15}/> SAVJ member profile · identity verification not yet available</p><div className="skill-list">{worker.skills.length ? worker.skills.map((item) => <span key={item}>{item}</span>) : <span>No skills listed</span>}</div><div className="onboarding-actions"><button className="secondary-button" onClick={onExplore}>Explore tasks</button></div></article>)}</div>
  </>;
}
