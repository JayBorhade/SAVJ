import React, { useEffect, useState } from 'react';
import { Save, ShieldCheck } from 'lucide-react';
import { savjApi, type ApiUser } from '../data/apiClient';

const availableSkills = ['Cleanup', 'Gardening', 'Plantation', 'Waste sorting', 'General helper', 'Cooking', 'Packing'];
const availableTools = ['Gloves', 'Shovel', 'Rake', 'Trash bags', 'Grabbers', 'Watering can', 'Saplings', 'Safety vest', 'Broom', 'Buckets'];
export default function LiveProfile({ user, onUpdated, onNotice }: { user: ApiUser; onUpdated: (user: ApiUser) => void; onNotice: (message: string) => void }) {
  const [name, setName] = useState(user.display_name);
  const [locality, setLocality] = useState(user.locality);
  const [purpose, setPurpose] = useState(user.purpose);
  const [skills, setSkills] = useState(user.skills.filter((skill) => availableSkills.includes(skill)));
  const [tools, setTools] = useState((user.tools || []).filter((tool) => availableTools.includes(tool)));
  const [customSkills, setCustomSkills] = useState(user.skills.filter((skill) => !availableSkills.includes(skill)).join(', '));
  const [customTools, setCustomTools] = useState((user.tools || []).filter((tool) => !availableTools.includes(tool)).join(', '));
  const [busy, setBusy] = useState(false);
  useEffect(() => { setName(user.display_name); setLocality(user.locality); setPurpose(user.purpose); setSkills(user.skills.filter((skill) => availableSkills.includes(skill))); setTools((user.tools || []).filter((tool) => availableTools.includes(tool))); setCustomSkills(user.skills.filter((skill) => !availableSkills.includes(skill)).join(', ')); setCustomTools((user.tools || []).filter((tool) => !availableTools.includes(tool)).join(', ')); }, [user]);
  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const parseList = (value: string) => [...new Set(value.split(',').map((item) => item.trim()).filter(Boolean))];
    const nextSkills = [...new Set([...skills, ...parseList(customSkills)])];
    const nextTools = [...new Set([...tools, ...parseList(customTools)])];
    if (nextSkills.length > 30 || nextTools.length > 30 || [...nextSkills, ...nextTools].some((item) => item.length > 80)) {
      onNotice('Use at most 30 skills and 30 tools; each entry must be 80 characters or fewer.');
      return;
    }
    setBusy(true);
    try {
      const updated = await savjApi.updateMe({ display_name: name.trim(), locality: locality.trim(), purpose, skills: nextSkills, tools: nextTools });
      onUpdated(updated); onNotice('Your SAVJ profile has been updated on the server.');
    } catch (error) { onNotice(error instanceof Error ? error.message : 'Could not update profile.'); }
    finally { setBusy(false); }
  };
  return <section className="section-card" style={{ maxWidth: 720, margin: '0 auto' }}><div className="section-heading"><div><h3>Your community profile</h3><p>Manage the profile connected to your SAVJ account.</p></div><ShieldCheck size={22}/></div><p><strong>Email:</strong> {user.email} <span className="status-badge status-completed">Account connected</span></p><form onSubmit={save}><label>Display name<input required minLength={1} maxLength={80} value={name} onChange={(e) => setName(e.target.value)}/></label><label>Locality<input required minLength={1} maxLength={160} value={locality} onChange={(e) => setLocality(e.target.value)}/></label><label>How do you want to contribute?<select value={purpose} onChange={(e) => setPurpose(e.target.value)}><option value="Requester">Requester</option><option value="Worker">Worker</option><option value="Both">Both</option></select></label><p className="onboarding-label">Skills</p><div className="onboarding-skills">{availableSkills.map((skill) => <button type="button" key={skill} className={skills.includes(skill) ? 'skill-option selected' : 'skill-option'} onClick={() => setSkills((current) => current.includes(skill) ? current.filter((item) => item !== skill) : [...current, skill])}>{skills.includes(skill) ? '✓ ' : '+ '}{skill}</button>)}</div><p className="onboarding-label">Tools you can use</p><div className="onboarding-skills">{availableTools.map((tool) => <button type="button" key={tool} className={tools.includes(tool) ? 'skill-option selected' : 'skill-option'} onClick={() => setTools((current) => current.includes(tool) ? current.filter((item) => item !== tool) : [...current, tool])}>{tools.includes(tool) ? '✓ ' : '+ '}{tool}</button>)}</div><label>Other skills (comma-separated)<input value={customSkills} onChange={(e) => setCustomSkills(e.target.value)} maxLength={2500} placeholder="e.g. First aid, Composting" /></label><label>Other tools (comma-separated)<input value={customTools} onChange={(e) => setCustomTools(e.target.value)} maxLength={2500} placeholder="e.g. Ladder, Wheelbarrow" /></label><div className="onboarding-actions"><button className="primary-button" type="submit" disabled={busy}>{busy ? 'Saving…' : <><Save size={16}/> Save profile</>}</button></div></form></section>;
}
