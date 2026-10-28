import React, { useEffect, useState } from 'react';
import { CheckCircle2, Sprout, TreePine, Recycle, Clock3 } from 'lucide-react';
import { savjApi } from '../data/apiClient';

type Impact = { verified_completed_tasks: number; community_drives_joined: number };
export default function LiveImpact({ backendConnected, onNotice }: { backendConnected: boolean; onNotice: (message: string) => void }) {
  const [impact, setImpact] = useState<Impact | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!backendConnected) return;
    let cancelled = false;
    setLoading(true);
    void savjApi.myImpact().then((data) => { if (!cancelled) setImpact(data); })
      .catch((error) => { if (!cancelled) onNotice(error instanceof Error ? error.message : 'Could not load verified impact.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [backendConnected, onNotice]);
  if (!backendConnected) return <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> EVERY ACTION COUNTS</div><h1>Your impact, in action</h1><p className="subheading">Sign in to view verified activity from your SAVJ account.</p></div></section><div className="demo-disclaimer">Impact figures are not invented or estimated while signed out.</div></>;
  return <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> EVERY ACTION COUNTS</div><h1>Your impact, in action</h1><p className="subheading">A little progress, repeated, can change a neighbourhood.</p></div><button className="secondary-button" onClick={() => { setLoading(true); void savjApi.myImpact().then(setImpact).catch((error) => onNotice(error instanceof Error ? error.message : 'Could not refresh impact.')).finally(() => setLoading(false)); }}>Refresh</button></section>
    {loading && <p role="status">Loading verified impact…</p>}
    <section className="stats-grid impact-stats"><Stat icon={<CheckCircle2 size={19}/>} label="Verified tasks completed" value={impact?.verified_completed_tasks} /><Stat icon={<Sprout size={19}/>} label="Community drives joined" value={impact?.community_drives_joined} /><Stat icon={<TreePine size={19}/>} label="Trees planted" value={null} /><Stat icon={<Recycle size={19}/>} label="Waste collected" value={null}/></section>
    <div className="section-card achievement-card"><div className="achievement-badge"><Sprout size={32}/></div><div><span className="eyebrow">VERIFIED CONTRIBUTIONS</span><h2>Your contribution history</h2><p>Counts include only backend-recorded activity. Tree counts, waste weights and volunteer hours are not yet collected by the system.</p></div></div>
    <section className="section-card impact-achievements"><div className="section-heading"><div><h3>Community medals</h3><p>Earned from verified task completions and recorded drive participation.</p></div></div><div className="medal-grid">
      {[
        { name: 'First Good Deed', description: 'Complete your first task', unlocked: (impact?.verified_completed_tasks || 0) >= 1, mark: '🌱' },
        { name: 'Green Volunteer', description: 'Join your first community drive', unlocked: (impact?.community_drives_joined || 0) >= 1, mark: '🌿' },
        { name: 'Community Helper', description: 'Complete five tasks', unlocked: (impact?.verified_completed_tasks || 0) >= 5, mark: '🤝' },
        { name: 'Earth Guardian', description: 'Complete ten tasks and join three drives', unlocked: (impact?.verified_completed_tasks || 0) >= 10 && (impact?.community_drives_joined || 0) >= 3, mark: '🌍' },
      ].map((medal) => <article className={medal.unlocked ? 'medal-card unlocked' : 'medal-card locked'} key={medal.name}><span className="medal-mark">{medal.mark}</span><div><strong>{medal.name}</strong><p>{medal.description}</p><small>{medal.unlocked ? 'Unlocked from verified activity' : 'Not unlocked yet'}</small></div></article>)}
    </div></section>
  </>;
}
function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: number | null | undefined }) {
  return <article className="stat-card"><div className="stat-top"><span className="stat-icon">{icon}</span><span className="stat-trend"><Clock3 size={14}/></span></div><div className="stat-value">{value == null ? 'Not tracked' : value.toLocaleString()}</div><div className="stat-label">{label}</div><div className="stat-change">{value == null ? 'No verified metric available' : 'From server records'}</div></article>;
}
