import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity, ArrowDownRight, ArrowRight, Bell, CalendarDays, CheckCircle2,
  ChevronDown, Compass, Filter, Flower2, HandHeart,
  Leaf, MapPin, MessageCircle, Plus, Search, Settings2, ShieldCheck,
  Sprout, TreePine, Users, X, Clock3, Recycle, Waves, Wind
} from 'lucide-react';
import './App.css';
import { transitionTaskStatus, validateTaskDraft, type TaskStatus } from './domain/taskWorkflow';
import { createBrowserTaskRepository } from './data/taskRepository';
import { clearAccessToken, getAccessToken, savjApi, type ApiTask, type ApiUser } from './data/apiClient';
import LiveCommunity from './components/LiveCommunity';
import LiveMessages from './components/LiveMessages';
import LiveImpact from './components/LiveImpact';
import LiveProfile from './components/LiveProfile';

type Task = {
  id: number; title: string; category: string; location: string; distance: number;
  budget: number; date: string; skills: string[]; status: TaskStatus;
  icon: 'leaf' | 'tree' | 'water' | 'recycle'; description: string;
  latitude?: number | null; longitude?: number | null;
};

const initialTasks: Task[] = [
  { id: 1, title: 'Clean up the neighborhood park', category: 'Community cleanup', location: 'Aundh, Pune', distance: 1.2, budget: 800, date: 'Today, 4:00 PM', skills: ['Cleanup', 'Teamwork'], status: 'Open', icon: 'leaf', description: 'Help collect litter, sort recyclables, and leave the park cleaner for everyone.' },
  { id: 2, title: 'Plant native trees along the lane', category: 'Tree plantation', location: 'Baner, Pune', distance: 2.4, budget: 1200, date: 'Tomorrow, 9:00 AM', skills: ['Gardening', 'Plantation'], status: 'Open', icon: 'tree', description: 'Plant and water native saplings with a small neighborhood group.' },
  { id: 3, title: 'Restore the community garden', category: 'Green spaces', location: 'Pashan, Pune', distance: 3.1, budget: 650, date: 'Sat, 10:30 AM', skills: ['Gardening', 'Cleanup'], status: 'In progress', icon: 'leaf', description: 'Remove weeds, prepare garden beds, and tidy the shared green space.' },
  { id: 4, title: 'Collect plastic near the lake', category: 'Waterbody cleanup', location: 'Pashan Lake, Pune', distance: 4.3, budget: 950, date: 'Sun, 7:30 AM', skills: ['Cleanup', 'Waste sorting'], status: 'Open', icon: 'water', description: 'Join a supervised cleanup focused on plastic waste around the lakeside.' },
];

const drives = [
  { title: 'Pashan Lake Clean-up', date: 'SUN, OCT 12 · 7:30 AM', place: 'Pashan Lake, Pune', joined: 24, kind: 'water' },
  { title: 'Green Pune: Native Trees', date: 'SAT, OCT 18 · 9:00 AM', place: 'Baner Biodiversity Park', joined: 38, kind: 'tree' },
];

function fromApiTask(task: ApiTask): Task {
  const date = task.scheduled_at ? new Date(task.scheduled_at).toLocaleString() : 'Schedule to be confirmed';
  const icon: Task['icon'] = /tree|plant/i.test(task.category + task.title) ? 'tree' : /water|lake/i.test(task.category + task.title) ? 'water' : /recycl|waste/i.test(task.category + task.title) ? 'recycle' : 'leaf';
  return { id: task.id, title: task.title, category: task.category, location: task.location_text, latitude: task.latitude, longitude: task.longitude, distance: 0, budget: task.budget_minor_units / 100, date, skills: [], status: task.status, icon, description: task.description };
}

function distanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const toRad = (value: number) => value * Math.PI / 180;
  const dLat = toRad(lat2 - lat1), dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 6371.0088 * 2 * Math.asin(Math.sqrt(Math.min(1, a)));
}

function TaskIcon({ kind }: { kind: Task['icon'] }) {
  if (kind === 'tree') return <TreePine size={21} />;
  if (kind === 'water') return <Waves size={21} />;
  if (kind === 'recycle') return <Recycle size={21} />;
  return <Leaf size={21} />;
}

export default function App() {
  const [activePage, setActivePage] = useState('Overview');
  const [profileName, setProfileName] = useState(() => localStorage.getItem('savj.profileName') || '');
  const [profileArea, setProfileArea] = useState(() => localStorage.getItem('savj.profileArea') || 'Pune, Maharashtra');
  const [purpose, setPurpose] = useState(() => localStorage.getItem('savj.purpose') || 'Both');
  const [onboardingDone, setOnboardingDone] = useState(() => localStorage.getItem('savj.onboardingDone') === 'true');
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [onboardingSkills, setOnboardingSkills] = useState<string[]>([]);
  const [tasks, setTasks] = useState<Task[]>(() => { try { const repository=createBrowserTaskRepository(); return localStorage.getItem('savj.tasks') ? repository.list() : initialTasks; } catch { return initialTasks; } });
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [beforeProofName, setBeforeProofName] = useState('');
  const [afterProofName, setAfterProofName] = useState('');
  const [beforeProofFile, setBeforeProofFile] = useState<File | null>(null);
  const [afterProofFile, setAfterProofFile] = useState<File | null>(null);
  const [search, setSearch] = useState('');
  const [radius, setRadius] = useState(5);
  const [currentCoordinates, setCurrentCoordinates] = useState<{ latitude: number; longitude: number } | null>(null);
  const [taskCoordinates, setTaskCoordinates] = useState<{ latitude: number; longitude: number } | null>(null);
  const [locationBusy, setLocationBusy] = useState(false);
  const [category, setCategory] = useState('All tasks');
  const [showPostModal, setShowPostModal] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [joinedDrives, setJoinedDrives] = useState<string[]>(() => { try { return JSON.parse(localStorage.getItem('savj.joinedDrives') || '[]') as string[]; } catch { return []; } });
  useEffect(() => { try { createBrowserTaskRepository().saveAll(tasks); } catch { /* Browser storage may be disabled; the UI remains usable for this session. */ } }, [tasks]);
  useEffect(() => { localStorage.setItem('savj.joinedDrives', JSON.stringify(joinedDrives)); }, [joinedDrives]);
  useEffect(() => { if (profileName.trim()) localStorage.setItem('savj.profileName', profileName.trim()); }, [profileName]);
  useEffect(() => { if (profileArea.trim()) localStorage.setItem('savj.profileArea', profileArea.trim()); }, [profileArea]);
  useEffect(() => {
    if (!getAccessToken()) return;
    let cancelled = false;
    void (async () => {
      try {
        const [user, apiTasks] = await Promise.all([savjApi.me(), savjApi.listTasks()]);
        if (cancelled) return;
        setApiUser(user); setBackendConnected(true); setProfileName(user.display_name); setProfileArea(user.locality); setPurpose(user.purpose);
        setTasks(apiTasks.map(fromApiTask));
        setNotice('Connected to SAVJ backend. Tasks are now loaded from the server.');
      } catch (error) { if (!cancelled) setNotice(error instanceof Error ? error.message : 'Could not restore your SAVJ session.'); }
    })();
    return () => { cancelled = true; };
  }, []);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskLocation, setTaskLocation] = useState('Pune, Maharashtra');
  const [taskBudget, setTaskBudget] = useState('500');
  const [taskDescription, setTaskDescription] = useState('');
  const [notice, setNotice] = useState('');
  const [apiUser, setApiUser] = useState<ApiUser | null>(null);
  const [apiEmail, setApiEmail] = useState('');
  const [apiPassword, setApiPassword] = useState('');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [apiBusy, setApiBusy] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);

  useEffect(() => {
    if (!backendConnected || !currentCoordinates) return;
    let cancelled = false;
    void savjApi.listTasks({ ...currentCoordinates, radius_km: radius })
      .then((apiTasks) => { if (!cancelled) setTasks(apiTasks.map(fromApiTask)); })
      .catch((error) => { if (!cancelled) setNotice(error instanceof Error ? error.message : 'Radius search failed.'); });
    return () => { cancelled = true; };
  }, [backendConnected, currentCoordinates, radius]);




  const filteredTasks = useMemo(() => tasks.map((task) => {
    const distance = currentCoordinates && task.latitude != null && task.longitude != null
      ? distanceKm(currentCoordinates.latitude, currentCoordinates.longitude, task.latitude, task.longitude)
      : task.distance;
    return { ...task, distance };
  }).filter((task) =>
    (currentCoordinates ? task.latitude != null && task.longitude != null && task.distance <= radius : task.distance <= radius) &&
    (category === 'All tasks' || task.category === category) &&
    (task.title + task.location + task.category + task.skills.join(' ')).toLowerCase().includes(search.toLowerCase())
  ), [tasks, radius, category, search, currentCoordinates]);

  const navigate = (page: string) => { setActivePage(page); setNotice(''); };
  const requestCurrentLocation = () => {
    if (!navigator.geolocation) { setNotice('This browser does not support location services.'); return; }
    setLocationBusy(true);
    navigator.geolocation.getCurrentPosition(
      (position) => { setCurrentCoordinates({ latitude: position.coords.latitude, longitude: position.coords.longitude }); setLocationBusy(false); setNotice('Location enabled. Radius discovery now uses real coordinates where available.'); },
      () => { setLocationBusy(false); setNotice('Location permission was unavailable. You can still browse tasks by area text.'); },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
    );
  };
  const tagTaskLocation = () => {
    if (!navigator.geolocation) { setNotice('This browser does not support location services.'); return; }
    setLocationBusy(true);
    navigator.geolocation.getCurrentPosition(
      (position) => { setTaskCoordinates({ latitude: position.coords.latitude, longitude: position.coords.longitude }); setLocationBusy(false); setNotice('Task location tagged with your current coordinates.'); },
      () => { setLocationBusy(false); setNotice('Could not access location. You can publish the task without coordinates.'); },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
    );
  };
  const joinDrive = (title: string) => {
    setJoinedDrives((current) => current.includes(title) ? current : [...current, title]);
    setNotice(backendConnected ? 'Community drive participation must be joined from a live drive record.' : 'You joined this drive in the local demo. This participation is saved only in this browser.');
  };
  const signInOrRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setApiBusy(true);
    try {
      const result = authMode === 'register'
        ? await savjApi.register({ email: apiEmail.trim(), password: apiPassword, display_name: profileName.trim() || apiEmail.split('@')[0], locality: profileArea.trim() || 'Pune, Maharashtra', purpose: purpose === 'Volunteer' ? 'Both' : purpose, skills: onboardingSkills })
        : await savjApi.login(apiEmail.trim(), apiPassword);
      setApiUser(result.user); setProfileName(result.user.display_name); setProfileArea(result.user.locality); setPurpose(result.user.purpose); setBackendConnected(true);
      const serverTasks = await savjApi.listTasks(); setTasks(serverTasks.map(fromApiTask));
      setApiPassword(''); setNotice('Signed in. SAVJ tasks are synced with the backend database.');
    } catch (error) { setNotice(error instanceof Error ? error.message : 'Authentication failed.'); }
    finally { setApiBusy(false); }
  };
  const signOut = () => { clearAccessToken(); setApiUser(null); setBackendConnected(false); setTasks(createBrowserTaskRepository().list().length ? createBrowserTaskRepository().list() : initialTasks); setNotice('Signed out. You are viewing the local demo again.'); };
  const postTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validation = validateTaskDraft({ title: taskTitle, location: taskLocation, budget: taskBudget });
    if (!validation.valid) { setNotice(Object.values(validation.errors).filter(Boolean).join(' ')); return; }
    if (backendConnected) {
      setApiBusy(true);
      try {
        const created = await savjApi.createTask({ title: taskTitle.trim(), description: taskDescription.trim(), category: 'Community cleanup', location_text: taskLocation.trim(), budget_rupees: validation.budget, latitude: taskCoordinates?.latitude ?? null, longitude: taskCoordinates?.longitude ?? null });
        const newTask = fromApiTask(created);
        setTasks((current) => [newTask, ...current]); setShowPostModal(false); setActivePage('Explore'); setSearch('');
        setTaskTitle(''); setTaskDescription(''); setTaskBudget('500'); setTaskCoordinates(null); setNotice('Task posted to the SAVJ backend.');
      } catch (error) { setNotice(error instanceof Error ? error.message : 'Could not post task.'); }
      finally { setApiBusy(false); }
      return;
    }
    const newTask: Task = createBrowserTaskRepository().create(
      { title: taskTitle, location: taskLocation, budget: validation.budget, description: taskDescription },
      { category: 'Community cleanup', distance: 1.5, date: 'Schedule to be confirmed', skills: ['Community'], status: 'Open', icon: 'leaf' },
    );
    setTasks((current) => [newTask, ...current]);
    setShowPostModal(false); setActivePage('Explore'); setSearch('');
    setTaskTitle(''); setTaskDescription(''); setTaskBudget('500'); setTaskCoordinates(null);
    setNotice('Your task has been added to the local demo feed.');
  };

  const navItems = [
    { label: 'Overview', icon: Activity },
    { label: 'Explore', icon: Compass },
    { label: 'Community', icon: Users },
    { label: 'Messages', icon: MessageCircle },
    { label: 'My impact', icon: Sprout },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => navigate('Overview')} aria-label="SAVJ home">
          <span className="brand-mark"><Leaf size={24} strokeWidth={2.4} /></span>
          <span className="brand-copy"><strong>SAVJ</strong><small>Greener & Cleaner India</small></span>
        </button>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map(({ label, icon: Icon }) => (
            <button key={label} className={activePage === label ? 'nav-item active' : 'nav-item'} onClick={() => navigate(label)}>
              <Icon size={19} /><span>{label}</span>
              {label === 'Messages' && <span className="nav-count">2</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <div className="impact-mini">
          <div className="impact-mini-icon"><Flower2 size={20} /></div>
          <p>Your impact is growing</p>
          <span>Every small action adds up.</span>
          <div className="mini-progress"><span /></div>
          <small>Level 2 · Green Neighbour</small>
        </div>
        <button className="nav-item settings-link" onClick={() => navigate('Settings')}><Settings2 size={19} /><span>Settings</span></button>
        <div className="profile-switch">
          <div className="avatar">{(profileName || 'Guest').slice(0,2).toUpperCase()}</div>
          <div className="profile-copy"><strong>{profileName || 'Guest user'}</strong><small>Demo profile</small></div>
          <ChevronDown size={16} className="muted" />
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><span className="crumb-slash">/</span><strong>{activePage}</strong></div>
          <div className="topbar-actions">
            <div className="location-pill"><MapPin size={15} /><span>{profileArea || 'Set your location'}</span><ChevronDown size={14} /></div>
            <div className="notification-wrap">
              <button className="icon-button" aria-label="Notifications" onClick={() => setShowNotifications(!showNotifications)}><Bell size={19} /><i /></button>
              {showNotifications && <div className="notification-popover"><strong>You’re all caught up</strong><p>New tasks and community updates will appear here.</p></div>}
            </div>
            <button className="top-avatar" aria-label="Open profile" onClick={() => navigate('Profile')}>{(profileName || 'G').slice(0,1).toUpperCase()}</button>
          </div>
        </header>

        <div className="page-content">
          {notice && <div className="notice-banner"><CheckCircle2 size={17} /><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss"><X size={16} /></button></div>}
          {activePage === 'Overview' && (
            <>
              <section className="welcome-row">
                <div><div className="eyebrow"><span className="eyebrow-dot" /> YOUR COMMUNITY, YOUR IMPACT</div><h1>Welcome{profileName ? `, ${profileName}` : ''} <span className="wave">✳</span></h1><p className="subheading">Small actions. Cleaner neighbourhoods. A greener tomorrow.</p></div>
                <button className="primary-button" onClick={() => setShowPostModal(true)}><Plus size={18} /> Post a task</button>
              </section>
              <section className="hero-card">
                <div className="hero-content"><div className="hero-tag"><Leaf size={14} /> YOUR GREEN JOURNEY</div><h2>Good things grow<br />when we <em>grow together.</em></h2><p>Find meaningful local tasks, lend a hand, and make your corner of India a little greener.</p><button className="hero-button" onClick={() => navigate('Explore')}>Explore nearby tasks <ArrowRight size={16} /></button></div>
                <div className="hero-art" aria-hidden="true"><div className="sun-disc" /><div className="art-hill hill-back" /><div className="art-hill hill-front" /><div className="art-tree tree-one"><span /><i /></div><div className="art-tree tree-two"><span /><i /></div><div className="art-leaf leaf-one"><Leaf size={42} /></div><div className="art-leaf leaf-two"><Leaf size={29} /></div><div className="art-sprout"><Sprout size={72} /></div></div>
              </section>
              <div className="demo-disclaimer"><ShieldCheck size={15} /> Preview data only — impact figures and sample opportunities are illustrative, not verified community totals.</div>
              <section className="stats-grid">
                <StatCard icon={<CheckCircle2 size={19} />} label="Tasks completed" value="Sample" change="Demo data" />
                <StatCard icon={<Clock3 size={19} />} label="Volunteer hours" value="Sample" change="Demo data" />
                <StatCard icon={<TreePine size={19} />} label="Trees planted" value="Sample" change="Demo data" />
                <StatCard icon={<Recycle size={19} />} label="Waste collected" value="Sample" change="Demo data" />
              </section>
              <section className="content-grid">
                <div className="section-card task-section">
                  <div className="section-heading"><div><h3>Tasks near you</h3><p>Make a difference right around the corner.</p></div><button className="text-link" onClick={() => navigate('Explore')}>View all <ArrowRight size={15} /></button></div>
                  <div className="task-list">{filteredTasks.slice(0, 3).map((task) => <TaskRow key={task.id} task={task} onOpen={() => setSelectedTask(task)} />)}</div>
                </div>
                <div className="section-card drives-section">
                  <div className="section-heading"><div><h3>Community drives</h3><p>Better together.</p></div><button className="round-arrow" onClick={() => navigate('Community')} aria-label="View community drives"><ArrowRight size={17} /></button></div>
                  {drives.map((drive, index) => <div className="drive-row" key={drive.title}><div className={'drive-image drive-image-' + index}>{index === 0 ? <Waves size={25} /> : <TreePine size={25} />}</div><div className="drive-info"><strong>{drive.title}</strong><span><CalendarDays size={13} /> {drive.date}</span><small><MapPin size={13} /> {drive.place}</small><button className={joinedDrives.includes(drive.title) ? 'join-link joined' : 'join-link'} onClick={() => joinDrive(drive.title)}>{joinedDrives.includes(drive.title) ? 'Joined ✓' : 'Join drive'} <ArrowRight size={13} /></button></div></div>)}
                </div>
              </section>
              <section className="bottom-quote"><div className="quote-icon"><HandHeart size={21} /></div><div><strong>One neighbourhood at a time.</strong><p>Every task you take on helps build a cleaner, more connected community.</p></div><button onClick={() => navigate('My impact')}>See your impact <ArrowRight size={15} /></button></section>
            </>
          )}

          {activePage === 'Explore' && (
            <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> FIND YOUR NEXT GOOD DEED</div><h1>Explore nearby tasks</h1><p className="subheading">Local opportunities to make a real difference.</p></div><button className="primary-button" onClick={() => setShowPostModal(true)}><Plus size={18} /> Post a task</button></section>
              <div className="explore-toolbar"><button className="secondary-button" onClick={requestCurrentLocation} disabled={locationBusy}>{locationBusy ? "Locating…" : currentCoordinates ? "Location enabled ✓" : "Use my location"}</button><div className="search-box"><Search size={18} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search tasks, skills, or locations..." /></div><div className="radius-control"><MapPin size={16} /><span>Within</span><select value={radius} onChange={(e) => setRadius(Number(e.target.value))} aria-label="Search radius"><option value={1}>1 km</option><option value={3}>3 km</option><option value={5}>5 km</option><option value={10}>10 km</option><option value={25}>25 km</option></select></div><div className="filter-control"><Filter size={16} /><select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Task category"><option>All tasks</option><option>Community cleanup</option><option>Tree plantation</option><option>Green spaces</option><option>Waterbody cleanup</option></select></div></div>
              <div className="explore-layout"><div className="explore-results"><div className="results-caption"><strong>{filteredTasks.length} opportunities</strong><span>Sorted by distance</span></div>{filteredTasks.map((task) => <TaskRow key={task.id} task={task} onOpen={() => setSelectedTask(task)} expanded />)}{filteredTasks.length === 0 && <div className="empty-state"><Leaf size={30} /><strong>No tasks match those filters</strong><p>Try a wider radius or a different search.</p><button className="secondary-button" onClick={() => { setRadius(10); setCategory('All tasks'); setSearch(''); }}>Clear filters</button></div>}</div>
                <div className="map-panel"><div className="map-header"><strong><MapPin size={16} /> Task map</strong><span>Illustrative preview</span></div><div className="map-canvas"><div className="map-water" /><div className="map-park park-a" /><div className="map-park park-b" /><div className="map-road road-a" /><div className="map-road road-b" /><div className="map-road road-c" /><span className="map-label label-a">AUNDH</span><span className="map-label label-b">BANER</span><span className="map-label label-c">PASHAN LAKE</span>{filteredTasks.slice(0, 4).map((task, i) => <button key={task.id} className={'map-pin pin-' + i} onClick={() => setNotice(task.title + ' · ' + task.distance + ' km away')} aria-label={'Select ' + task.title}><Leaf size={15} /></button>)}<div className="map-home"><MapPin size={18} /></div></div><div className="map-legend"><span><i className="legend-dot" /> Open tasks</span><span><i className="legend-home" /> Your area</span></div><p className="map-note">{currentCoordinates ? "Radius filtering uses your browser location and coordinates stored on tasks. Tasks without coordinates are omitted from radius results." : "Enable location to calculate real distances. The illustrated map still needs a configured map-tile provider."}</p></div></div>
            </>
          )}

          {activePage === 'Community' && <LiveCommunity backendConnected={backendConnected} onNotice={setNotice} />}

          {activePage === 'Messages' && <LiveMessages backendConnected={backendConnected} currentUser={apiUser} onNotice={setNotice} />}
          {activePage === 'My impact' && <LiveImpact backendConnected={backendConnected} onNotice={setNotice} />}
          {(activePage === 'Settings' || activePage === 'Profile') && (activePage === 'Profile' ? (apiUser && backendConnected ? <LiveProfile user={apiUser} onUpdated={(user) => { setApiUser(user); setProfileName(user.display_name); setProfileArea(user.locality); setPurpose(user.purpose); }} onNotice={setNotice} /> : <SimplePage icon={<ShieldCheck size={28} />} title="Your community profile" description="Sign in to manage your server-backed profile." action="Open settings" onAction={() => navigate('Settings')} />) : <section className="section-card" style={{ maxWidth: 680, margin: '0 auto' }}><div className="section-heading"><div><h3>Backend connection</h3><p>Connect this interface to your local SAVJ API.</p></div><span className={backendConnected ? 'status-badge status-completed' : 'status-badge'}>{backendConnected ? 'Connected' : 'Demo mode'}</span></div><p className="subheading">API address: {import.meta.env.VITE_SAVJ_API_URL || 'http://127.0.0.1:8000'}</p>{apiUser ? <><p>Signed in as <strong>{apiUser.display_name}</strong> ({apiUser.email}). Task listings and new tasks use the backend database.</p><button className="secondary-button" onClick={signOut}>Sign out</button></> : <form className="post-modal" style={{ position: 'static', width: '100%', maxWidth: 'none', boxShadow: 'none', padding: 0, marginTop: 20 }} onSubmit={signInOrRegister}><div className="onboarding-options"><button type="button" className={authMode === 'login' ? 'onboarding-choice selected' : 'onboarding-choice'} onClick={() => setAuthMode('login')}>Sign in</button><button type="button" className={authMode === 'register' ? 'onboarding-choice selected' : 'onboarding-choice'} onClick={() => setAuthMode('register')}>Create account</button></div><label>Email<input type="email" required value={apiEmail} onChange={(event) => setApiEmail(event.target.value)} autoComplete="email" /></label><label>Password<input type="password" required minLength={authMode === 'register' ? 10 : 1} maxLength={128} value={apiPassword} onChange={(event) => setApiPassword(event.target.value)} autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} /></label><p className="modal-footnote">{authMode === 'register' ? 'Use at least 10 characters. Your password is sent to your configured backend over your local connection.' : 'Sign in to load your server-backed tasks.'}</p><button className="primary-button" type="submit" disabled={apiBusy}>{apiBusy ? 'Connecting…' : authMode === 'register' ? 'Create account' : 'Sign in'} <ArrowRight size={16}/></button></form>}</section>)}
        </div>
      </main>

      {!onboardingDone && <div className="modal-backdrop onboarding-backdrop"><form className="post-modal onboarding-modal" onSubmit={(e) => { e.preventDefault(); if (onboardingStep === 0) { if (!profileName.trim() || !profileArea.trim()) { setNotice('Please enter your name and area.'); return; } setOnboardingStep(1); return; } if (onboardingStep === 1) { setOnboardingStep(2); return; } localStorage.setItem('savj.onboardingDone','true'); localStorage.setItem('savj.purpose',purpose); setOnboardingDone(true); setNotice('Welcome to SAVJ demo, ' + profileName.trim() + '! Your profile is saved in this browser.'); }}><div className="modal-heading"><div><span className="eyebrow">WELCOME TO SAVJ · STEP {onboardingStep+1} OF 3</span><h2>{onboardingStep===0?'Let’s get to know you':onboardingStep===1?'How would you like to contribute?':'Make SAVJ yours'}</h2><p>{onboardingStep===0?'Set up your local demo profile.':onboardingStep===1?'You can change this preference later.':'Choose skills to personalize task discovery.'}</p></div></div>{onboardingStep===0 ? <><label>Your name<input required maxLength={60} value={profileName} onChange={(e)=>setProfileName(e.target.value)} placeholder="Enter your name" /></label><label>Your area or locality<input required maxLength={100} value={profileArea} onChange={(e)=>setProfileArea(e.target.value)} placeholder="e.g. Pune, Maharashtra" /></label></> : onboardingStep===1 ? <div className="onboarding-options">{['Requester','Worker','Volunteer','Both'].map((item)=><button type="button" key={item} className={purpose===item?'onboarding-choice selected':'onboarding-choice'} onClick={()=>setPurpose(item)}><strong>{item}</strong><span>{item==='Requester'?'Post tasks for your neighbourhood':item==='Worker'?'Discover paid local tasks':item==='Volunteer'?'Join environmental drives':'Post, work and volunteer'}</span></button>)}</div> : <><p className="onboarding-label">Your skills (optional)</p><div className="onboarding-skills">{['Cleanup','Gardening','Plantation','Waste sorting','General helper'].map((skill)=><button type="button" key={skill} className={onboardingSkills.includes(skill)?'skill-option selected':'skill-option'} onClick={()=>setOnboardingSkills((old)=>old.includes(skill)?old.filter((x)=>x!==skill):[...old,skill])}>{onboardingSkills.includes(skill)?'✓ ': '+ '}{skill}</button>)}</div><p className="modal-footnote">Demo only: profile data stays in this browser. Sign-in, KYC and backend sync are not connected.</p></>}<div className="onboarding-actions">{onboardingStep>0&&<button type="button" className="secondary-button" onClick={()=>setOnboardingStep((n)=>n-1)}>Back</button>}<button className="primary-button submit-task" type="submit">{onboardingStep===2?'Finish setup':'Continue'} <ArrowRight size={16}/></button></div></form></div>}
      {selectedTask && <div className="modal-backdrop" onMouseDown={(e)=>{if(e.target===e.currentTarget)setSelectedTask(null)}}><section className="post-modal"><div className="modal-heading"><div><span className="eyebrow">TASK DETAILS · DEMO</span><h2>{selectedTask.title}</h2><p>{selectedTask.category} · {selectedTask.distance} km away</p></div><button type="button" className="icon-button" onClick={()=>setSelectedTask(null)} aria-label="Close task details"><X size={20}/></button></div><p>{selectedTask.description}</p><div className="task-detail-meta"><span><MapPin size={15}/> {selectedTask.location}</span><span><CalendarDays size={15}/> {selectedTask.date}</span><strong>₹{selectedTask.budget.toLocaleString('en-IN')}</strong></div><p><strong>Skills:</strong> {selectedTask.skills.join(', ')}</p><p><strong>Status:</strong> {selectedTask.status}</p>
      {selectedTask.status==='In progress'&&<div className="proof-fields"><label>Before photo (required)<input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={(e)=>{const file=e.target.files?.[0]||null;setBeforeProofFile(file);setBeforeProofName(file?.name||'');}}/></label><label>After photo (required)<input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={(e)=>{const file=e.target.files?.[0]||null;setAfterProofFile(file);setAfterProofName(file?.name||'');}}/></label><small>Images upload to private backend storage (JPEG, PNG or WebP; max 8 MB each) when signed in. Demo mode only checks file selection.</small></div>}
      <div className="demo-disclaimer"><ShieldCheck size={15}/> Task actions use the backend when connected. Proof uploads are private and participant-authorized; requester notifications and KYC verification are not implemented.</div>
      <div className="onboarding-actions"><button type="button" className="secondary-button" onClick={()=>setSelectedTask(null)}>Close</button>
      {selectedTask.status==='Open'&&<button type="button" className="primary-button" onClick={async()=>{if(backendConnected){try{const updated=fromApiTask(await savjApi.transitionTask(selectedTask.id,'accept'));setTasks((all)=>all.map((t)=>t.id===updated.id?updated:t));setSelectedTask(updated);setNotice('Task accepted by the SAVJ backend.');}catch(error){setNotice(error instanceof Error?error.message:'Could not accept task.');}return;}const result=transitionTaskStatus(selectedTask.status,'Accepted');if(!result.ok){setNotice(result.reason);return;}setTasks((all)=>all.map((t)=>t.id===selectedTask.id?{...t,status:result.status}:t));setSelectedTask({...selectedTask,status:result.status});setNotice('Task accepted in this browser demo. No requester has been notified.');}}>{backendConnected?'Accept task':'Accept in demo'}</button>}
      {selectedTask.status==='Accepted'&&<button type="button" className="primary-button" onClick={async()=>{if(backendConnected){try{const updated=fromApiTask(await savjApi.transitionTask(selectedTask.id,'start'));setTasks((all)=>all.map((t)=>t.id===updated.id?updated:t));setSelectedTask(updated);setNotice('Task started on the backend.');}catch(error){setNotice(error instanceof Error?error.message:'Could not start task.');}return;}const result=transitionTaskStatus(selectedTask.status,'In progress');if(!result.ok){setNotice(result.reason);return;}setTasks((all)=>all.map((t)=>t.id===selectedTask.id?{...t,status:result.status}:t));setSelectedTask({...selectedTask,status:result.status});}}>Start task {backendConnected?'':'(demo)'}</button>}
      {selectedTask.status==='In progress'&&<button type="button" className="primary-button" disabled={!beforeProofName||!afterProofName} onClick={async()=>{if(backendConnected){if(!beforeProofFile||!afterProofFile){setNotice('Choose both before and after images.');return;}try{await savjApi.uploadProof(selectedTask.id,'before',beforeProofFile);await savjApi.uploadProof(selectedTask.id,'after',afterProofFile);const updated=fromApiTask(await savjApi.transitionTask(selectedTask.id,'submit'));setTasks((all)=>all.map((t)=>t.id===updated.id?updated:t));setSelectedTask(updated);setBeforeProofFile(null);setAfterProofFile(null);setBeforeProofName('');setAfterProofName('');setNotice('Before and after proof images uploaded securely. Task submitted for requester approval.');}catch(error){setNotice(error instanceof Error?error.message:'Could not upload proof images.');}return;}const result=transitionTaskStatus(selectedTask.status,'Awaiting approval');if(!result.ok){setNotice(result.reason);return;}setTasks((all)=>all.map((t)=>t.id===selectedTask.id?{...t,status:result.status}:t));setSelectedTask({...selectedTask,status:result.status});setNotice('Both proof files selected. Nothing was uploaded; task awaits demo approval.');}}>Submit proof {backendConnected?'(uploads not ready)':'(demo)'}</button>}
      {selectedTask.status==='Awaiting approval'&&<button type="button" className="primary-button" onClick={async()=>{if(backendConnected){try{const updated=fromApiTask(await savjApi.transitionTask(selectedTask.id,'approve'));setTasks((all)=>all.map((t)=>t.id===updated.id?updated:t));setSelectedTask(updated);setNotice('Completion approved by the backend.');}catch(error){setNotice(error instanceof Error?error.message:'Could not approve task.');}return;}const result=transitionTaskStatus(selectedTask.status,'Completed');if(!result.ok){setNotice(result.reason);return;}setTasks((all)=>all.map((t)=>t.id===selectedTask.id?{...t,status:result.status}:t));setSelectedTask({...selectedTask,status:result.status});setNotice('Demo task marked complete. No real requester approval was recorded.');}}>{backendConnected?'Approve completion':'Simulate requester approval'}</button>}
      </div></section></div>}
      {showPostModal && <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setShowPostModal(false); }}><form className="post-modal" onSubmit={postTask}><div className="modal-heading"><div><span className="eyebrow">START SOMETHING GOOD</span><h2>Post a community task</h2><p>Tell your neighbourhood what needs doing.</p></div><button type="button" className="icon-button" onClick={() => setShowPostModal(false)} aria-label="Close modal"><X size={20} /></button></div><label>Task title<input required value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="e.g. Clean our society garden" /></label><label>Location<input required value={taskLocation} onChange={(e) => setTaskLocation(e.target.value)} placeholder="Area or neighbourhood" /></label><label>Budget (₹)<input type="number" min="0" value={taskBudget} onChange={(e) => setTaskBudget(e.target.value)} /></label><button type="button" className="secondary-button" onClick={tagTaskLocation} disabled={locationBusy}>{taskCoordinates ? "Task location tagged ✓" : "Tag task at my current location"}</button><p className="modal-footnote">Coordinates are optional and only attached when you explicitly tag this task.</p><label>What needs to be done?<textarea value={taskDescription} onChange={(e) => setTaskDescription(e.target.value)} placeholder="Add details, expectations, or timing..." rows={3} /></label><div className="modal-footnote"><ShieldCheck size={16} /> Keep task details clear and community-friendly.</div><button className="primary-button submit-task" type="submit"><Plus size={17} /> Publish task to demo feed</button></form></div>}
    </div>
  );
}

function StatCard({ icon, label, value, change }: { icon: React.ReactNode; label: string; value: string; change: string }) {
  return <article className="stat-card"><div className="stat-top"><span className="stat-icon">{icon}</span><span className="stat-trend"><ArrowDownRight size={14} /></span></div><div className="stat-value">{value}</div><div className="stat-label">{label}</div><div className="stat-change">{change}</div></article>;
}
function TaskRow({ task, onOpen, expanded = false }: { task: Task; onOpen: () => void; expanded?: boolean }) {
  return <article className={expanded ? 'task-row task-row-expanded' : 'task-row'}><div className={'task-icon task-icon-' + task.icon}><TaskIcon kind={task.icon} /></div><div className="task-main"><div className="task-title-line"><strong>{task.title}</strong><span className={task.status === 'Open' ? 'status-chip open' : 'status-chip progress'}>{task.status}</span></div><span className="task-category">{task.category}</span><div className="task-meta"><span><MapPin size={13} /> {task.location}</span><span><Compass size={13} /> {task.distance} km</span><span><CalendarDays size={13} /> {task.date}</span></div>{expanded && <><p className="task-description">{task.description}</p><div className="skill-list">{task.skills.map((skill) => <span key={skill}>{skill}</span>)}</div></>}</div><div className="task-end"><strong>₹{task.budget.toLocaleString('en-IN')}</strong><small>{task.budget ? 'Budget' : 'Volunteer'}</small><button onClick={onOpen} aria-label={'View ' + task.title}><ArrowRight size={17} /></button></div></article>;
}
function SimplePage({ icon, title, description, action, onAction }: { icon: React.ReactNode; title: string; description: string; action: string; onAction: () => void }) {
  return <div className="simple-page"><div className="simple-page-icon">{icon}</div><h1>{title}</h1><p>{description}</p><button className="primary-button" onClick={onAction}>{action} <ArrowRight size={16} /></button><div className="coming-soon"><Wind size={18} /> Built in milestones — core navigation is ready, and deeper workflows are next.</div></div>;
}
