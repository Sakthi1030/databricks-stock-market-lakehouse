import "@testing-library/jest-dom/vitest";

// jsdom's own localStorage doesn't reliably initialize under this Node/Vitest/jsdom version
// combination (Node 26 ships an experimental native `localStorage` global that shadows
// jsdom's). A minimal in-memory implementation sidesteps the ambiguity entirely rather than
// depending on exactly which one "wins" in a given environment.
class MemoryStorage implements Storage {
  private store = new Map<string, string>();

  get length() {
    return this.store.size;
  }

  clear() {
    this.store.clear();
  }

  getItem(key: string) {
    return this.store.has(key) ? this.store.get(key)! : null;
  }

  setItem(key: string, value: string) {
    this.store.set(key, String(value));
  }

  removeItem(key: string) {
    this.store.delete(key);
  }

  key(index: number) {
    return Array.from(this.store.keys())[index] ?? null;
  }
}

Object.defineProperty(window, "localStorage", {
  value: new MemoryStorage(),
  writable: true,
});
