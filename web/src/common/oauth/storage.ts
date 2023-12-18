import { WebStorageStateStore } from "oidc-client-ts";

export class MemoryStore extends WebStorageStateStore {
    private map: Map<string, string> = new Map();
    async set(key: string, value: string): Promise<void> {
        this.map.set(key, value);
    }
    async get(key: string): Promise<string | null> {
        const value = this.map.get(key);
        return value ? value : null;
    }
    async remove(key: string): Promise<string | null> {
        const value = await this.get(key);
        this.map.delete(key);
        return value;
    }
    async getAllKeys(): Promise<string[]> {
        return Array.from(this.map.keys());
    }
}
