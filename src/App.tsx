import { useMemo, useState } from 'react';
import {
  Activity, ArrowDownRight, ArrowRight, Bell, CalendarDays, CheckCircle2,
  ChevronDown, CircleHelp, Compass, Filter, Flower2, HandHeart, Heart,
  Leaf, MapPin, Menu, MessageCircle, Plus, Search, Settings2, ShieldCheck,
  Sprout, TreePine, Users, Wallet, X, Clock3, Recycle, Waves, Wind
} from 'lucide-react';
import './App.css';

type Task = {
  id: number; title: string; category: string; location: string; distance: number;
  budget: number; date: string; skills: string[]; status: 'Open' | 'In progress';
  icon: 'leaf' | 'tree' | 'water' | 'recycle'; description: string;
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

function TaskIcon({ kind }: { kind: Task['icon'] }) {
  if (kind === 'tree') return <TreePine size={21} />;
  if (kind === 'water') return <Waves size={21} />;
  if (kind === 'recycle') return <Recycle size={21} />;
  return <Leaf size={21} />;
}

export default function App() {
  const [activePage, setActivePage] = useState('Overview');
  const [tasks, setTasks] = useState(initialTasks);
  const [search, setSearch] = useState('');
  const [radius, setRadius] = useState(5);
  const [category, setCategory] = useState('All tasks');
  const [showPostModal, setShowPostModal] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [joinedDrives, setJoinedDrives] = useState<string[]>([]);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskLocation, setTaskLocation] = useState('Pune, Maharashtra');
  const [taskBudget, setTaskBudget] = useState('500');
  const [taskDescription, setTaskDescription] = useState('');
  const [notice, setNotice] = useState('');

  const filteredTasks = useMemo(() => tasks.filter((task) =>
    task.distance <= radius &&
    (category === 'All tasks' || task.category === category) &&
    (task.title + task.location + task.category + task.skills.join(' ')).toLowerCase().includes(search.toLowerCase())
  ), [tasks, radius, category, search]);

  const navigate = (page: string) => { setActivePage(page); setNotice(''); };
  const joinDrive = (title: string) => {
    setJoinedDrives((current) => current.includes(title) ? current : [...current, title]);
    setNotice('You’re on the list! Drive details are ready in your community activity.');
  };
  const postTask = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!taskTitle.trim() || !taskLocation.trim()) return;
    const newTask: Task = {
      id: Date.now(), title: taskTitle.trim(), category: 'Community cleanup',
      location: taskLocation.trim(), distance: 1.5, budget: Math.max(0, Number(taskBudget) || 0),
      date: 'Schedule to be confirmed', skills: ['Community'], status: 'Open', icon: 'leaf',
      description: taskDescription.trim() || 'A new local task posted by the community.'
    };
    setTasks((current) => [newTask, ...current]);
    setShowPostModal(false); setActivePage('Explore'); setSearch('');
    setTaskTitle(''); setTaskDescription(''); setTaskBudget('500');
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
          <div className="avatar">JB</div>
          <div className="profile-copy"><strong>Jay Borhade</strong><small>Community member</small></div>
          <ChevronDown size={16} className="muted" />
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><span className="crumb-slash">/</span><strong>{activePage}</strong></div>
          <div className="topbar-actions">
            <div className="location-pill"><MapPin size={15} /><span>Pune, Maharashtra</span><ChevronDown size={14} /></div>
            <div className="notification-wrap">
              <button className="icon-button" aria-label="Notifications" onClick={() => setShowNotifications(!showNotifications)}><Bell size={19} /><i /></button>
              {showNotifications && <div className="notification-popover"><strong>You’re all caught up</strong><p>New tasks and community updates will appear here.</p></div>}
            </div>
            <button className="top-avatar" aria-label="Open profile" onClick={() => navigate('Profile')}>JB</button>
          </div>
        </header>

        <div className="page-content">
          {notice && <div className="notice-banner"><CheckCircle2 size={17} /><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss"><X size={16} /></button></div>}
          {activePage === 'Overview' && (
            <>
              <section className="welcome-row">
                <div><div className="eyebrow"><span className="eyebrow-dot" /> YOUR COMMUNITY, YOUR IMPACT</div><h1>Welcome back, Jay <span className="wave">✳</span></h1><p className="subheading">Small actions. Cleaner neighbourhoods. A greener tomorrow.</p></div>
                <button className="primary-button" onClick={() => setShowPostModal(true)}><Plus size={18} /> Post a task</button>
              </section>
              <section className="hero-card">
                <div className="hero-content"><div className="hero-tag"><Leaf size={14} /> YOUR GREEN JOURNEY</div><h2>Good things grow<br />when we <em>grow together.</em></h2><p>Find meaningful local tasks, lend a hand, and make your corner of India a little greener.</p><button className="hero-button" onClick={() => navigate('Explore')}>Explore nearby tasks <ArrowRight size={16} /></button></div>
                <div className="hero-art" aria-hidden="true"><div className="sun-disc" /><div className="art-hill hill-back" /><div className="art-hill hill-front" /><div className="art-tree tree-one"><span /><i /></div><div className="art-tree tree-two"><span /><i /></div><div className="art-leaf leaf-one"><Leaf size={42} /></div><div className="art-leaf leaf-two"><Leaf size={29} /></div><div className="art-sprout"><Sprout size={72} /></div></div>
              </section>
              <section className="stats-grid">
                <StatCard icon={<CheckCircle2 size={19} />} label="Tasks completed" value="12" change="+3 this month" />
                <StatCard icon={<Clock3 size={19} />} label="Volunteer hours" value="18.5" change="+4.5 this month" />
                <StatCard icon={<TreePine size={19} />} label="Trees planted" value="24" change="Across 3 drives" />
                <StatCard icon={<Recycle size={19} />} label="Waste collected" value="32 kg" change="Community total" />
              </section>
              <section className="content-grid">
                <div className="section-card task-section">
                  <div className="section-heading"><div><h3>Tasks near you</h3><p>Make a difference right around the corner.</p></div><button className="text-link" onClick={() => navigate('Explore')}>View all <ArrowRight size={15} /></button></div>
                  <div className="task-list">{filteredTasks.slice(0, 3).map((task) => <TaskRow key={task.id} task={task} onOpen={() => { setActivePage('Explore'); setSearch(task.title); }} />)}</div>
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
              <div className="explore-toolbar"><div className="search-box"><Search size={18} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search tasks, skills, or locations..." /></div><div className="radius-control"><MapPin size={16} /><span>Within</span><select value={radius} onChange={(e) => setRadius(Number(e.target.value))} aria-label="Search radius"><option value={1}>1 km</option><option value={3}>3 km</option><option value={5}>5 km</option><option value={10}>10 km</option><option value={25}>25 km</option></select></div><div className="filter-control"><Filter size={16} /><select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Task category"><option>All tasks</option><option>Community cleanup</option><option>Tree plantation</option><option>Green spaces</option><option>Waterbody cleanup</option></select></div></div>
              <div className="explore-layout"><div className="explore-results"><div className="results-caption"><strong>{filteredTasks.length} opportunities</strong><span>Sorted by distance</span></div>{filteredTasks.map((task) => <TaskRow key={task.id} task={task} onOpen={() => setNotice('Task selected: ' + task.title + '. Requirement checks and task acceptance will be connected in the next workflow batch.')} expanded />)}{filteredTasks.length === 0 && <div className="empty-state"><Leaf size={30} /><strong>No tasks match those filters</strong><p>Try a wider radius or a different search.</p><button className="secondary-button" onClick={() => { setRadius(10); setCategory('All tasks'); setSearch(''); }}>Clear filters</button></div>}</div>
                <div className="map-panel"><div className="map-header"><strong><MapPin size={16} /> Task map</strong><span>Illustrative preview</span></div><div className="map-canvas"><div className="map-water" /><div className="map-park park-a" /><div className="map-park park-b" /><div className="map-road road-a" /><div className="map-road road-b" /><div className="map-road road-c" /><span className="map-label label-a">AUNDH</span><span className="map-label label-b">BANER</span><span className="map-label label-c">PASHAN LAKE</span>{filteredTasks.slice(0, 4).map((task, i) => <button key={task.id} className={'map-pin pin-' + i} onClick={() => setNotice(task.title + ' · ' + task.distance + ' km away')} aria-label={'Select ' + task.title}><Leaf size={15} /></button>)}<div className="map-home"><MapPin size={18} /></div></div><div className="map-legend"><span><i className="legend-dot" /> Open tasks</span><span><i className="legend-home" /> Your area</span></div><p className="map-note">Map is a visual placeholder. Live geocoding and map tiles will be connected in the integration milestone.</p></div></div>
            </>
          )}

          {activePage === 'Community' && <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> MAKE CHANGE TOGETHER</div><h1>Community drives</h1><p className="subheading">Show up for your neighbourhood and the planet.</p></div></section><div className="community-banner"><div><HandHeart size={28} /><h2>Good work grows in good company.</h2><p>Join local cleanups, plantation events, and community-led environmental action.</p></div><div className="community-banner-art"><TreePine size={90} /><Sprout size={55} /></div></div><div className="drive-cards">{drives.map((drive, i) => <article className="drive-card" key={drive.title}><div className={'drive-card-art art-' + i}>{i === 0 ? <Waves size={44} /> : <TreePine size={44} />}<span>{i === 0 ? 'WATERBODY CARE' : 'URBAN GREENING'}</span></div><div className="drive-card-body"><span className="event-date"><CalendarDays size={14} /> {drive.date}</span><h3>{drive.title}</h3><p><MapPin size={14} /> {drive.place}</p><div className="drive-card-footer"><span><Users size={15} /> {drive.joined + (joinedDrives.includes(drive.title) ? 1 : 0)} people joining</span><button className={joinedDrives.includes(drive.title) ? 'secondary-button' : 'primary-button'} onClick={() => joinDrive(drive.title)}>{joinedDrives.includes(drive.title) ? 'You’re joining' : 'Join drive'}</button></div></div></article>)}</div></>}

          {activePage === 'Messages' && <SimplePage icon={<MessageCircle size={28} />} title="Your conversations" description="Task-based conversations will live here so requesters and workers can coordinate clearly." action="Explore tasks" onAction={() => navigate('Explore')} />}
          {activePage === 'My impact' && <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> EVERY ACTION COUNTS</div><h1>Your impact, in action</h1><p className="subheading">A little progress, repeated, can change a neighbourhood.</p></div></section><section className="stats-grid impact-stats"><StatCard icon={<CheckCircle2 size={19} />} label="Tasks completed" value="12" change="All-time total" /><StatCard icon={<Clock3 size={19} />} label="Volunteer hours" value="18.5" change="Time given back" /><StatCard icon={<TreePine size={19} />} label="Trees planted" value="24" change="Across 3 drives" /><StatCard icon={<Recycle size={19} />} label="Waste collected" value="32 kg" change="Community total" /></section><div className="section-card achievement-card"><div className="achievement-badge"><Sprout size={32} /></div><div><span className="eyebrow">CURRENT ACHIEVEMENT</span><h2>Green Neighbour · Level 2</h2><p>Keep showing up. Your next milestone is 20 completed tasks.</p><div className="achievement-progress"><span /></div><small>12 of 20 tasks completed</small></div></div><div className="section-card"><div className="section-heading"><div><h3>Your contribution history</h3><p>Recent community activity</p></div></div><div className="history-row"><span className="history-icon"><Leaf size={18} /></span><div><strong>Neighbourhood park cleanup</strong><p>Community cleanup · Aundh</p></div><span className="history-date">Oct 04</span><span className="status-chip complete">Completed</span></div><div className="history-row"><span className="history-icon"><TreePine size={18} /></span><div><strong>Native sapling plantation</strong><p>Community drive · Baner</p></div><span className="history-date">Sep 28</span><span className="status-chip complete">Completed</span></div></div></>}
          {(activePage === 'Settings' || activePage === 'Profile') && <SimplePage icon={<ShieldCheck size={28} />} title={activePage === 'Profile' ? 'Your community profile' : 'Settings & preferences'} description="Profile verification, skills, preferred radius, and account preferences will be configured here in the identity and trust milestone." action="Back to overview" onAction={() => navigate('Overview')} />}
        </div>
      </main>

      {showPostModal && <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setShowPostModal(false); }}><form className="post-modal" onSubmit={postTask}><div className="modal-heading"><div><span className="eyebrow">START SOMETHING GOOD</span><h2>Post a community task</h2><p>Tell your neighbourhood what needs doing.</p></div><button type="button" className="icon-button" onClick={() => setShowPostModal(false)} aria-label="Close modal"><X size={20} /></button></div><label>Task title<input required value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="e.g. Clean our society garden" /></label><label>Location<input required value={taskLocation} onChange={(e) => setTaskLocation(e.target.value)} placeholder="Area or neighbourhood" /></label><label>Budget (₹)<input type="number" min="0" value={taskBudget} onChange={(e) => setTaskBudget(e.target.value)} /></label><label>What needs to be done?<textarea value={taskDescription} onChange={(e) => setTaskDescription(e.target.value)} placeholder="Add details, expectations, or timing..." rows={3} /></label><div className="modal-footnote"><ShieldCheck size={16} /> Keep task details clear and community-friendly.</div><button className="primary-button submit-task" type="submit"><Plus size={17} /> Publish task to demo feed</button></form></div>}
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
