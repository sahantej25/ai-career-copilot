import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// Tests must not depend on frontend/.env (gitignored, not in GitHub).
vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "");
vi.stubEnv("VITE_API_URL", "");

const storage = new Map<string, string>();

const sessionStorageMock: Storage = {
  get length() {
    return storage.size;
  },
  clear() {
    storage.clear();
  },
  getItem(key: string) {
    return storage.has(key) ? storage.get(key)! : null;
  },
  key(index: number) {
    return Array.from(storage.keys())[index] ?? null;
  },
  removeItem(key: string) {
    storage.delete(key);
  },
  setItem(key: string, value: string) {
    storage.set(key, value);
  },
};

Object.defineProperty(window, "sessionStorage", { value: sessionStorageMock });

beforeEach(() => {
  storage.clear();
});
