import { json, rejectCrossSite } from "../../../../lib/http";
import { clearSessionCookie } from "../../../../lib/session";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const blocked = rejectCrossSite(req);
  if (blocked) return blocked;
  return json({ ok: true }, 200, { "Set-Cookie": clearSessionCookie(req) });
}
