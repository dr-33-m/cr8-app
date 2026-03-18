import type { Storage } from "@logto/node";
import type { useSession } from "@tanstack/react-start/server";

type SessionManager = Awaited<ReturnType<typeof useSession<Record<string, string>>>>;

/**
 * Bridges @logto/node's Storage interface to TanStack Start's session manager.
 * Each setItem/removeItem call persists via the session cookie.
 */
export class LogtoSessionStorage implements Storage<string> {
  private manager: SessionManager;

  constructor(manager: SessionManager) {
    this.manager = manager;
  }

  async getItem(key: string): Promise<string | null> {
    const value = this.manager.data[key];
    return value ?? null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.manager = await this.manager.update({ [key]: value });
  }

  async removeItem(key: string): Promise<void> {
    this.manager = await this.manager.update((old) => {
      const copy = { ...old };
      delete copy[key];
      return copy;
    });
  }
}
