export const json = (body: unknown, status = 200, extra?: HeadersInit) =>
  Response.json(body, {
    status,
    headers: {
      "Cache-Control": "private, no-store",
      Vary: "Cookie",
      "X-Content-Type-Options": "nosniff",
      ...extra,
    },
  });

function expectedOrigin(req: Request): string {
  const configured = process.env.APP_ORIGIN?.trim();
  if (configured) return new URL(configured).origin;

  const url = new URL(req.url);
  const forwardedHost = req.headers.get("x-forwarded-host")?.split(",")[0]?.trim();
  const host = forwardedHost || req.headers.get("host");
  const forwardedProto = req.headers.get("x-forwarded-proto")?.split(",")[0]?.trim();
  const protocol = forwardedProto === "http" || forwardedProto === "https"
    ? forwardedProto
    : url.protocol.slice(0, -1);

  return host ? new URL(`${protocol}://${host}`).origin : url.origin;
}

export function rejectCrossSite(req: Request): Response | null {
  if (req.headers.get("sec-fetch-site") === "cross-site") {
    return json({ error: "Cross-site changes are not allowed." }, 403);
  }
  const origin = req.headers.get("origin");
  if (origin) {
    try {
      if (new URL(origin).origin !== expectedOrigin(req)) {
        return json({ error: "Request origin did not match this site." }, 403);
      }
    } catch {
      return json({ error: "Request origin did not match this site." }, 403);
    }
  }
  return null;
}

export async function readJson(req: Request, maxBytes = 32_768): Promise<{ data: unknown } | { error: Response }> {
  if (!req.headers.get("content-type")?.includes("application/json")) {
    return { error: json({ error: "Expected a JSON request." }, 415) };
  }
  const reader = req.body?.getReader();
  if (!reader) return { error: json({ error: "Missing request body." }, 400) };
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > maxBytes) {
      await reader.cancel();
      return { error: json({ error: "This submission is too large." }, 413) };
    }
    chunks.push(value);
  }
  try {
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.length;
    }
    return { data: JSON.parse(new TextDecoder().decode(bytes)) };
  } catch {
    return { error: json({ error: "Invalid JSON." }, 400) };
  }
}
