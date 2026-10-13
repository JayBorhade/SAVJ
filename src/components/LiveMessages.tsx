import React, { useCallback, useEffect, useState } from 'react';
import { MessageCircle, Send } from 'lucide-react';
import { savjApi, type ApiMessage, type ApiTask, type ApiUser } from '../data/apiClient';

type Props = { backendConnected: boolean; currentUser: ApiUser | null; onNotice: (message: string) => void };

export default function LiveMessages({ backendConnected, currentUser, onNotice }: Props) {
  const [tasks, setTasks] = useState<ApiTask[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ApiMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const loadTasks = useCallback(async () => {
    if (!backendConnected || !currentUser) return;
    setLoading(true);
    try {
      const all = await savjApi.listTasks();
      const participantTasks = all.filter((task) => task.requester_id === currentUser.id || task.worker_id === currentUser.id);
      setTasks(participantTasks);
      setSelectedId((current) => current && participantTasks.some((task) => task.id === current) ? current : participantTasks[0]?.id ?? null);
    } catch (error) { onNotice(error instanceof Error ? error.message : 'Could not load conversations.'); }
    finally { setLoading(false); }
  }, [backendConnected, currentUser, onNotice]);
  const loadMessages = useCallback(async () => {
    if (!selectedId || !backendConnected) { setMessages([]); return; }
    try { setMessages(await savjApi.listMessages(selectedId)); }
    catch (error) { onNotice(error instanceof Error ? error.message : 'Could not load task messages.'); }
  }, [backendConnected, onNotice, selectedId]);
  useEffect(() => { void loadTasks(); }, [loadTasks]);
  useEffect(() => { void loadMessages(); }, [loadMessages]);

  const send = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const body = draft.trim();
    if (!body || !selectedId || sending) return;
    setSending(true);
    try { const message = await savjApi.sendMessage(selectedId, body); setMessages((current) => [...current, message]); setDraft(''); }
    catch (error) { onNotice(error instanceof Error ? error.message : 'Could not send message.'); }
    finally { setSending(false); }
  };

  if (!backendConnected || !currentUser) return <div className="simple-page"><div className="simple-page-icon"><MessageCircle size={28} /></div><h1>Your conversations</h1><p>Sign in to see task conversations. Messages are only available to the requester and assigned worker.</p><div className="coming-soon">Open Settings to connect your SAVJ account.</div></div>;
  const selectedTask = tasks.find((task) => task.id === selectedId);
  return <><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot" /> COORDINATE WITH YOUR COMMUNITY</div><h1>Your conversations</h1><p className="subheading">Keep task coordination clear and connected.</p></div><button className="secondary-button" onClick={() => { void loadTasks(); void loadMessages(); }}>Refresh</button></section>
    {loading && <p role="status">Loading conversations…</p>}
    {!loading && tasks.length === 0 && <div className="section-card"><h3>No task conversations yet</h3><p>Accept a task or post one and wait for a worker to join. Only task participants can message each other.</p></div>}
    {tasks.length > 0 && <div className="content-grid" style={{ gridTemplateColumns: 'minmax(220px, 0.8fr) minmax(0, 1.5fr)' }}><section className="section-card"><div className="section-heading"><div><h3>Tasks</h3><p>Your active conversations</p></div></div>{tasks.map((task) => <button key={task.id} className={task.id === selectedId ? 'onboarding-choice selected' : 'onboarding-choice'} style={{ width: '100%', marginBottom: 8, textAlign: 'left' }} onClick={() => setSelectedId(task.id)}><strong>{task.title}</strong><span>{task.status} · #{task.id}</span></button>)}</section><section className="section-card"><div className="section-heading"><div><h3>{selectedTask?.title ?? 'Messages'}</h3><p>Messages are visible only to task participants.</p></div></div><div aria-live="polite" style={{ minHeight: 180, maxHeight: 420, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10, padding: 8 }}>{messages.map((message) => <div key={message.id} style={{ alignSelf: message.sender_id === currentUser.id ? 'flex-end' : 'flex-start', maxWidth: '85%', borderRadius: 12, padding: '10px 12px', background: message.sender_id === currentUser.id ? '#e5f3e8' : '#f2f4f0' }}><p style={{ margin: 0, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{message.body}</p><small>{new Date(message.created_at).toLocaleString()}</small></div>)}</div><form onSubmit={send} style={{ display: 'flex', gap: 8, marginTop: 12 }}><input aria-label="Write a message" required maxLength={2000} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Write a message…" /><button className="primary-button" type="submit" disabled={!draft.trim() || sending || !selectedId}>{sending ? 'Sending…' : <><Send size={16} /> Send</>}</button></form></section></div>}
  </>;
}
