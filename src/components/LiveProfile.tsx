import React, { useEffect, useState } from 'react';
import { Save, ShieldCheck } from 'lucide-react';
import { savjApi, type ApiUser } from '../data/apiClient';

const availableSkills = ['Cleanup', 'Gardening', 'Plantation', 'Waste sorting', 'General helper', 'Cooking', 'Packing'];
export default function LiveProfile({ user, onUpdated, onNotice }: { user: ApiUser; onUpdated: (user: ApiUser) => void; onNotice: (message: string) => void }) {
  const [name, setName] = useState(user.display_name);
  const [locality, setLocality] = useState(user.locality);
  const [purpose, setPurpose] = useState(user.purpose);
  const [skills, setSkills] = useState(user.skills);
  const [busy, setBusy] = useState(false);
  useEffect(() => { setName(user.display_name); setLocality(user.locality); setPurpose(user.purpose); setSkills(user.skills); }, [user]);
  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true);
    try {
      const updated = await savjApi.updateMe({ display_name: name.trim(), locality: locality.trim(), purpose, skills });
      onUpdated(updated); onNotice('Your SAVJ profile has been updated on the server.');
    } catch (error) { onNotice(error instanceof Error ? error.message : 'Could not update profile.'); }
    finally { setBusy(false); }
  };
  return <section className="section-card" style={{ maxWidth: 720, margin: '0 auto' }}><div className="section-heading"><div><h3>Your community profile</h3><p>Manage the profile connected to your SAVJ account.</p></div><ShieldCheck size={22}/></div><p><strong>Email:</strong> {user.email} <span className="status-badge status-completed">Account connected</span></p><form onSubmit={save}><label>Display name<input required minLength={1} maxLength={80} value={name} onChange={(e) => setName(e.target.value)}/></label><label>Locality<input required minLength={1} maxLength={160} value={locality} onChange={(e) => setLocality(e.target.value)}/></label><label>How do you want to contribute?<select value={purpose} onChange={(e) => setPurpose(e.target.value)}><option value="Requester">Requester</option><option value="Worker">Worker</option><option value="Both">Both</option></select></label><p className="onboarding-label">Skills</p><div className="onboarding-skills">{availableSkills.map((skill) => <button type="button" key={skill} className={skills.includes(skill) ? 'skill-option selected' : 'skill-option'} onClick={() => setSkills((current) => current.includes(skill) ? current.filter((item) => item !== skill) : [...current, skill])}>{skills.includes(skill) ? '✓ ' : '+ '}{skill}</button>)}</div><div className="onboarding-actions"><button className="primary-button" type="submit" disabled={busy}>{busy ? 'Saving…' : <><Save size={16}/> Save profile</>}</button></div></form></section>;
}
