import { StoreError, type Database } from "./store.ts";
import { getDatabase } from "./database.ts";
import { sessionFromRequest, sessionSecret } from "./session.ts";

export type Identity = {
  owner: string;
  email: string | null;
  name: string | null;
  method: "session" | "chatgpt";
};

function chatgptIdentity(req: Request): Identity | null {
  const owner = req.headers.get("oai-authenticated-user-id")?.trim();
  if (!owner) return null;
  return {
    owner,
    email: req.headers.get("oai-authenticated-user-email"),
    name: req.headers.get("oai-authenticated-user-full-name"),
    method: "chatgpt",
  };
}

export async function getIdentity(req: Request): Promise<Identity> {
  const session = await sessionFromRequest(req);
  if (session) {
    return { owner: session.uid, email: session.email, name: session.name, method: "session" };
  }
  const chatgpt = chatgptIdentity(req);
  if (chatgpt) return chatgpt;
  if (process.env.VERCEL === "1" && !sessionSecret()) {
    throw new StoreError("This host needs SESSION_SECRET configured for organizer sign-in.", 503);
  }
  throw new StoreError("Sign in to load your saved workspace.", 401);
}

export async function requireWorkspaceContext(req: Request): Promise<{ owner: string; db: Database; identity: Identity }> {
  const identity = await getIdentity(req);
  return { owner: identity.owner, db: await getDatabase(), identity };
}
