export interface TokenStorage {
  read: () => Promise<string | null>;
  write: (token: string | null) => Promise<void>;
}

export class TokenStore {
  private storage: TokenStorage;
  private token: string | null = null;
  private loaded = false;
  private generation = 0;
  private writes: Promise<void> = Promise.resolve();
  constructor(storage: TokenStorage) { this.storage = storage; }

  read = async (): Promise<string | null> => {
    if (this.loaded) return this.token;
    const version = this.generation;
    const value = await this.storage.read();
    if (version === this.generation) { this.token = value; this.loaded = true; }
    return this.token;
  };

  write = (token: string | null): Promise<void> => {
    ++this.generation;
    this.token = token;
    this.loaded = true;
    // Keep persisted ordering identical to session ordering, including sign-out races.
    const write = this.writes.catch(() => {}).then(() => this.storage.write(token));
    this.writes = write;
    return write;
  };
}
