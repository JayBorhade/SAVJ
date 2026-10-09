export const TASK_STATUSES = [
  'Open',
  'Accepted',
  'In progress',
  'Awaiting approval',
  'Completed',
  'Cancelled',
] as const;

export type TaskStatus = (typeof TASK_STATUSES)[number];

export type TaskTransitionResult =
  | { ok: true; status: TaskStatus }
  | { ok: false; reason: string };

const ALLOWED_TRANSITIONS: Record<TaskStatus, readonly TaskStatus[]> = {
  Open: ['Accepted', 'Cancelled'],
  Accepted: ['In progress', 'Cancelled'],
  'In progress': ['Awaiting approval', 'Cancelled'],
  'Awaiting approval': ['Completed', 'In progress'],
  Completed: [],
  Cancelled: [],
};

/** Returns whether a status change is valid for the SAVJ task lifecycle. */
export function canTransitionTask(from: TaskStatus, to: TaskStatus): boolean {
  return ALLOWED_TRANSITIONS[from].includes(to);
}

/** Validates a requested transition and returns a safe result for UI/API callers. */
export function transitionTaskStatus(from: TaskStatus, to: TaskStatus): TaskTransitionResult {
  if (canTransitionTask(from, to)) return { ok: true, status: to };
  return {
    ok: false,
    reason: `A task cannot move from "${from}" to "${to}".`,
  };
}

export type TaskDraft = {
  title: string;
  location: string;
  budget: string | number;
  description?: string;
  date?: string;
};

export type TaskDraftValidation =
  | { valid: true; budget: number }
  | { valid: false; errors: Partial<Record<'title' | 'location' | 'budget' | 'date', string>> };

/** Shared validation for task forms; safe to reuse from frontend and API handlers. */
export function validateTaskDraft(draft: TaskDraft): TaskDraftValidation {
  const errors: Partial<Record<'title' | 'location' | 'budget' | 'date', string>> = {};
  const budget = typeof draft.budget === 'number' ? draft.budget : Number(draft.budget);

  if (!draft.title.trim()) errors.title = 'Enter a task title.';
  if (!draft.location.trim()) errors.location = 'Enter a task location.';
  if (String(draft.budget).trim() === '' || !Number.isFinite(budget) || budget < 0) {
    errors.budget = 'Budget must be a valid non-negative number.';
  }
  if (draft.date !== undefined && !draft.date.trim()) errors.date = 'Choose a schedule.';
  if (Object.keys(errors).length) return { valid: false, errors };
  return { valid: true, budget };
}
