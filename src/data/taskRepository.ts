import type { TaskDraft } from '../domain/taskWorkflow';

/**
 * Persistence boundary for task records.
 * A future HTTP implementation can satisfy this contract without changing UI components.
 */
export type SavjTaskRecord = {
  id: number;
  title: string;
  category: string;
  location: string;
  distance: number;
  budget: number;
  date: string;
  skills: string[];
  status: import('../domain/taskWorkflow').TaskStatus;
  icon: 'leaf' | 'tree' | 'water' | 'recycle';
  description: string;
};

export interface TaskRepository {
  list(): SavjTaskRecord[];
  saveAll(tasks: SavjTaskRecord[]): void;
  create(draft: TaskDraft, defaults: Omit<SavjTaskRecord, 'id' | 'title' | 'location' | 'budget' | 'description'> & { description?: string }): SavjTaskRecord;
}

const TASKS_KEY = 'savj.tasks';

/** Browser-only prototype adapter. Not shared, secure, or suitable for production persistence. */
export class LocalStorageTaskRepository implements TaskRepository {
  constructor(private readonly storage: Pick<Storage, 'getItem' | 'setItem'>) {}

  list(): SavjTaskRecord[] {
    try {
      const value = this.storage.getItem(TASKS_KEY);
      if (!value) return [];
      const parsed: unknown = JSON.parse(value);
      return Array.isArray(parsed) ? parsed as SavjTaskRecord[] : [];
    } catch {
      return [];
    }
  }

  saveAll(tasks: SavjTaskRecord[]): void {
    this.storage.setItem(TASKS_KEY, JSON.stringify(tasks));
  }

  create(
    draft: TaskDraft,
    defaults: Omit<SavjTaskRecord, 'id' | 'title' | 'location' | 'budget' | 'description'> & { description?: string },
  ): SavjTaskRecord {
    const record = {
      ...defaults,
      id: Date.now(),
      title: draft.title.trim(),
      location: draft.location.trim(),
      budget: Number(draft.budget),
      description: draft.description?.trim() || 'A new local task posted by the community.',
    };
    return record;
  }
}

/** Construct the browser adapter only in client-side code. */
export function createBrowserTaskRepository(): LocalStorageTaskRepository {
  return new LocalStorageTaskRepository(window.localStorage);
}
