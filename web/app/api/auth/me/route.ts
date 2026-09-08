import { json } from "../../../../lib/http";
import { getIdentity } from "../../../../lib/identity";
import { StoreError } from "../../../../lib/store";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  try {
    const identity = await getIdentity(req);
    return json({
      id: identity.owner,
      email: identity.email,
      displayName: identity.name ?? identity.email ?? "Organizer",
      method: identity.method,
    });
  } catch (e) {
    if (e instanceof StoreError) return json({ error: e.message }, e.status);
    return json({ error: "Sign in to load your saved workspace." }, 401);
  }
}
