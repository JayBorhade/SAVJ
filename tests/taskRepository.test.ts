import test from 'node:test';
import assert from 'node:assert/strict';
import { LocalStorageTaskRepository } from '../src/data/taskRepository';

function createMemoryStorage() {
  const values = new Map<string, string>();
  return {
    getItem(key: string) {
      return values.get(key) ?? null;
    },
    setItem(key: string, value: string) {
      values.set(key, value);
    },
  };
}

const defaults = {
  category: 'Cleaning',
  distance: 2,
  date: 'Today',
  skills: ['Cleaner'],
  status: 'Open' as const,
  icon: 'leaf' as const,
};

test('repository starts empty and round-trips task records', () => {
  const storage = createMemoryStorage();
  const repository = new LocalStorageTaskRepository(storage);
  assert.deepEqual(repository.list(), []);
  const task = repository.create(
    { title: '  Clean the lake  ', location: '  Pune  ', budget: '300', description: '  Remove litter  ' },
    defaults,
  );
  assert.equal(task.title, 'Clean the lake');
  assert.equal(task.location, 'Pune');
  assert.equal(task.budget, 300);
  assert.equal(task.description, 'Remove litter');
  repository.saveAll([task]);
  assert.deepEqual(repository.list(), [task]);
});

test('repository handles malformed stored JSON without crashing', () => {
  const storage = createMemoryStorage();
  storage.setItem('savj.tasks', '{broken');
  assert.deepEqual(new LocalStorageTaskRepository(storage).list(), []);
});

test('repository supplies a safe default description when omitted', () => {
  const repository = new LocalStorageTaskRepository(createMemoryStorage());
  const task = repository.create({ title: 'Plant trees', location: 'Alandi', budget: 0 }, defaults);
  assert.equal(task.description, 'A new local task posted by the community.');
  assert.equal(task.budget, 0);
});
