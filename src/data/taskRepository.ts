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

function isSavjTaskRecord(value: unknown): value is SavjTaskRecord {
  if (typeof value !== 'object' || value === null) return false;
  const task = value as Record<string, unknown>;
  const validStatuses: readonly string[] = ['Open', 'Accepted', 'In progress', 'Awaiting approval', 'Completed', 'Cancelled'];
  const validIcons: readonly string[] = ['leaf', 'tree', 'water', 'recycle'];
  return Number.isFinite(task.id)
    && typeof task.title === 'string'
    && typeof task.category === 'string'
    && typeof task.location === 'string'
    && typeof task.distance === 'number' && Number.isFinite(task.distance)
    && typeof task.budget === 'number' && Number.isFinite(task.budget) && task.budget >= 0
    && typeof task.date === 'string'
    && Array.isArray(task.skills) && task.skills.every((skill) => typeof skill === 'string')
    && typeof task.status === 'string' && validStatuses.includes(task.status)
    && typeof task.icon === 'string' && validIcons.includes(task.icon)
    && typeof task.description === 'string';
}

/** Browser-only prototype adapter. Not shared, secure, or suitable for production persistence. */
export class LocalStorageTaskRepository implements TaskRepository {
  constructor(private readonly storage: Pick<Storage, 'getItem' | 'setItem'>) {}

  list(): SavjTaskRecord[] {
    try {
      const value = this.storage.getItem(TASKS_KEY);
      if (!value) return [];
      const parsed: unknown = JSON.parse(value);
      return Array.isArray(parsed) ? parsed.filter(isSavjTaskRecord) : [];
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
