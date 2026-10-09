import React, { useEffect, useState } from 'react';
import { Image, LoaderCircle } from 'lucide-react';
import { savjApi, type ApiTaskProof } from '../data/apiClient';

type Item = { proof: ApiTaskProof; url: string };
export default function TaskProofViewer({ taskId, onNotice }: { taskId: number; onNotice: (message: string) => void }) {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    let cancelled = false;
    const urls: string[] = [];
    setLoading(true);
    void (async () => {
      try {
        const proofs = await savjApi.listProofs(taskId);
        const loaded = await Promise.all(proofs.map(async (proof) => {
          const blob = await savjApi.downloadProof(proof.id);
          const url = URL.createObjectURL(blob);
          urls.push(url);
          return { proof, url };
        }));
        if (cancelled) urls.forEach((url) => URL.revokeObjectURL(url));
        else setItems(loaded);
      } catch (error) {
        if (!cancelled) onNotice(error instanceof Error ? error.message : 'Could not load task proof images.');
      } finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; urls.forEach((url) => URL.revokeObjectURL(url)); };
  }, [taskId, onNotice]);
  return <section className="section-card" style={{ marginTop: 16 }}><div className="section-heading"><div><h3><Image size={17} /> Submitted proof</h3><p>Images are fetched through participant-authorized endpoints.</p></div></div>
    {loading && <p role="status"><LoaderCircle size={15} /> Loading proof images…</p>}
    {!loading && items.length === 0 && <p>No proof images have been uploaded for this task yet.</p>}
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>{items.map(({ proof, url }) => <figure key={proof.id} style={{ margin: 0 }}><img src={url} alt={proof.proof_kind + ' work proof'} style={{ display: 'block', width: '100%', maxHeight: 260, objectFit: 'contain', borderRadius: 10, background: '#f2f4f0' }}/><figcaption style={{ marginTop: 6, fontSize: 13 }}><strong>{proof.proof_kind === 'before' ? 'Before' : 'After'}</strong> · {proof.original_name} · {(proof.size_bytes / 1024).toFixed(0)} KB</figcaption></figure>)}</div>
  </section>;
}
