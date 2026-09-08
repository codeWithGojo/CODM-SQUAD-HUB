import { AccountError, authenticateAccount } from "../../../../lib/accounts";
import { getDatabase } from "../../../../lib/database";
import { json, readJson, rejectCrossSite } from "../../../../lib/http";
import { sessionCookie, signSession } from "../../../../lib/session";
import { StoreError } from "../../../../lib/store";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const blocked = rejectCrossSite(req);
    if (blocked) return blocked;
    const parsed = await readJson(req, 8_192);
    if ("error" in parsed) return parsed.error;
    const body = (parsed.data ?? {}) as { email?: unknown; password?: unknown };
    const account = await authenticateAccount(await getDatabase(), body);
    const token = await signSession({ uid: account.id, email: account.email, name: account.display_name });
    return json(
      { id: account.id, email: account.email, displayName: account.display_name, method: "session" },
      200,
      { "Set-Cookie": sessionCookie(token, req) },
    );
  } catch (e) {
    if (e instanceof AccountError) return json({ error: e.message }, e.status);
    if (e instanceof StoreError) return json({ error: e.message }, e.status);
    if (e instanceof Error && e.message.includes("SESSION_SECRET")) {
      return json({ error: "This host needs SESSION_SECRET configured for organizer sign-in." }, 503);
    }
    console.error("Login failed", e instanceof Error ? e.message : "unknown error");
    return json({ error: "Could not sign in." }, 503);
  }
}
