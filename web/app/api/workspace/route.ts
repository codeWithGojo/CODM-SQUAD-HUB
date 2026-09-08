import { defaultGame } from "../../../lib/games";
import { json, readJson, rejectCrossSite } from "../../../lib/http";
import { requireWorkspaceContext } from "../../../lib/identity";
import { DomainError } from "../../../lib/workspace";
import { readWorkspace, saveCommand, StoreError } from "../../../lib/store";

export const dynamic = "force-dynamic";

function error(e: unknown) {
  if (e instanceof StoreError) return json({ error: e.message }, e.status);
  if (e instanceof DomainError) return json({ error: e.message }, 400);
  console.error("Workspace operation failed", e instanceof Error ? e.message : "unknown error");
  return json({ error: "Could not access saved records. Please try again; your input has been kept." }, 503);
}

export async function GET(req: Request) {
  try {
    const { owner, db } = await requireWorkspaceContext(req);
    const game = new URL(req.url).searchParams.get("game");
    if (!game) {
      const { results } = await db.prepare(
        "SELECT game, json_extract(body, '$.rules.name') AS name, updated_at FROM workspaces WHERE owner = ? ORDER BY updated_at DESC LIMIT 100",
      ).bind(owner).all<{ game: string; name: string; updated_at: string }>();
      return json({ games: results });
    }
    try { defaultGame(game); } catch { return json({ error: "Unknown game." }, 400); }
    return json(await readWorkspace(db, owner, game));
  } catch (e) {
    return error(e);
  }
}

export async function POST(req: Request) {
  try {
    const { owner, db } = await requireWorkspaceContext(req);
    const blocked = rejectCrossSite(req);
    if (blocked) return blocked;
    const parsed = await readJson(req);
    if ("error" in parsed) return parsed.error;
    const data = parsed.data as { game?: unknown; command?: unknown; version?: unknown; owner?: unknown };
    if (!data || typeof data.game !== "string" || !data.command || typeof data.command !== "object") {
      return json({ error: "Invalid workspace action." }, 400);
    }
    try { defaultGame(data.game); } catch { return json({ error: "Unknown game." }, 400); }
    return json(await saveCommand(db, owner, data.game, data.version as number, data.command as { type: string }));
  } catch (e) {
    return error(e);
  }
}
