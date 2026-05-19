import { create } from "zustand";

export interface QueuedItem {
  id: string;
  text: string;
}

type QueueStore = {
  queues: Record<string, QueuedItem[]>;
  enqueue: (sessionId: string, text: string) => void;
  removeFromQueue: (sessionId: string, id: string) => void;
  editQueueItem: (sessionId: string, id: string, text: string) => void;
  moveQueueItemUp: (sessionId: string, id: string) => void;
  dequeue: (sessionId: string) => QueuedItem | undefined;
  clearQueue: (sessionId: string) => void;
};

export const useQueueStore = create<QueueStore>((set, get) => ({
  queues: {},
  enqueue: (sessionId, text) =>
    set((s) => ({
      queues: {
        ...s.queues,
        [sessionId]: [...(s.queues[sessionId] ?? []), { id: crypto.randomUUID(), text }],
      },
    })),
  removeFromQueue: (sessionId, id) =>
    set((s) => ({
      queues: {
        ...s.queues,
        [sessionId]: (s.queues[sessionId] ?? []).filter((q) => q.id !== id),
      },
    })),
  editQueueItem: (sessionId, id, text) =>
    set((s) => ({
      queues: {
        ...s.queues,
        [sessionId]: (s.queues[sessionId] ?? []).map((q) =>
          q.id === id ? { ...q, text } : q
        ),
      },
    })),
  moveQueueItemUp: (sessionId, id) =>
    set((s) => {
      const queue = s.queues[sessionId] ?? [];
      const idx = queue.findIndex((q) => q.id === id);
      if (idx <= 0) return s;
      const next = [...queue];
      [next[idx - 1], next[idx]] = [next[idx], next[idx - 1]];
      return { queues: { ...s.queues, [sessionId]: next } };
    }),
  dequeue: (sessionId) => {
    const { queues } = get();
    const queue = queues[sessionId] ?? [];
    if (queue.length === 0) return undefined;
    const [first, ...rest] = queue;
    set({ queues: { ...queues, [sessionId]: rest } });
    return first;
  },
  clearQueue: (sessionId) =>
    set((s) => {
      const next = { ...s.queues };
      delete next[sessionId];
      return { queues: next };
    }),
}));
