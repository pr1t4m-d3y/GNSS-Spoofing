import { NextRequest, NextResponse } from "next/server";

// Same-origin proxy to the detector API. It keeps the API key on the server and lets the
// browser call `/api/...` without CORS. Only the routes the dashboard uses are forwarded.
export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const API_KEY = process.env.GNSS_API_KEY;

const GET_ROUTES = new Set(["scan", "health"]);
const POST_ROUTES = new Set(["predict", "predict/batch", "predict/file", "reset"]);

async function forward(
  request: NextRequest,
  { params }: { params: { path: string[] } },
): Promise<NextResponse> {
  const route = params.path.join("/");
  const allowed = request.method === "GET" ? GET_ROUTES : POST_ROUTES;
  if (!allowed.has(route)) {
    return NextResponse.json({ detail: "Not found." }, { status: 404 });
  }

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  if (API_KEY) headers.set("x-api-key", API_KEY);

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}/${route}`, {
      method: request.method,
      headers,
      body: request.method === "GET" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Detector API is unreachable." }, { status: 502 });
  }

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" },
  });
}

export { forward as GET, forward as POST };
