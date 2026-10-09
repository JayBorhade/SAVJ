import test from 'node:test';
import assert from 'node:assert/strict';
import { canTransitionTask, transitionTaskStatus, validateTaskDraft } from '../src/domain/taskWorkflow';

test('allows only the declared forward task transitions', () => {
  assert.equal(canTransitionTask('Open', 'Accepted'), true);
  assert.equal(canTransitionTask('Accepted', 'In progress'), true);
  assert.equal(canTransitionTask('In progress', 'Awaiting approval'), true);
  assert.equal(canTransitionTask('Awaiting approval', 'Completed'), true);
  assert.equal(canTransitionTask('Awaiting approval', 'In progress'), true);
});

test('rejects skipping workflow stages and reopening terminal tasks', () => {
  assert.equal(canTransitionTask('Open', 'Completed'), false);
  assert.equal(canTransitionTask('Accepted', 'Completed'), false);
  assert.equal(canTransitionTask('Completed', 'In progress'), false);
  assert.equal(canTransitionTask('Cancelled', 'Accepted'), false);
  assert.deepEqual(transitionTaskStatus('Open', 'Completed'), {
    ok: false,
    reason: 'A task cannot move from "Open" to "Completed".',
  });
});

test('permits cancellation before completion only', () => {
  assert.equal(canTransitionTask('Open', 'Cancelled'), true);
  assert.equal(canTransitionTask('Accepted', 'Cancelled'), true);
  assert.equal(canTransitionTask('In progress', 'Cancelled'), true);
  assert.equal(canTransitionTask('Completed', 'Cancelled'), false);
});

test('accepts valid task draft and normalizes numeric budget', () => {
  assert.deepEqual(validateTaskDraft({ title: '  Clean park ', location: ' Baner ', budget: '250' }), {
    valid: true,
    budget: 250,
  });
});

test('rejects blank title/location, invalid budget, and negative budget', () => {
  const result = validateTaskDraft({ title: ' ', location: '', budget: '-1' });
  assert.equal(result.valid, false);
  if (!result.valid) {
    assert.ok(result.errors.title);
    assert.ok(result.errors.location);
    assert.ok(result.errors.budget);
  }
  assert.equal(validateTaskDraft({ title: 'Task', location: 'Pune', budget: 'NaN' }).valid, false);
  assert.equal(validateTaskDraft({ title: 'Task', location: 'Pune', budget: '' }).valid, false);
});

test('rejects a blank schedule when one is supplied', () => {
  const result = validateTaskDraft({ title: 'Task', location: 'Pune', budget: 0, date: ' ' });
  assert.equal(result.valid, false);
  if (!result.valid) assert.ok(result.errors.date);
});
