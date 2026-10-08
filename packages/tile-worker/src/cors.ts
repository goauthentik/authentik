const EXPOSED_HEADERS = ["Accept-Ranges", "Content-Length", "ETag", "Range"].join(", ");
const ALLOWED_HEADERS = [
    "Accept",
    "Accept-Encoding",
    "Cache-Control",
    "If-Match",
    "If-Modified-Since",
    "If-None-Match",
    "Range",
].join(", ");

export interface CorsOptions {
    allowedOrigins: string;
}

function parseAllowed(spec: string): { wildcard: boolean; entries: string[] } {
    const trimmed = spec.trim();
    if (!trimmed || trimmed === "*") return { wildcard: true, entries: [] };
    const entries = trimmed
        .split(",")
        .map((part) => part.trim())
        .filter(Boolean);
    return { wildcard: false, entries };
}

export function applyCors(request: Request, response: Response, options: CorsOptions): void {
    const { wildcard, entries } = parseAllowed(options.allowedOrigins);

    if (wildcard) {
        response.headers.set("Access-Control-Allow-Origin", "*");
    } else {
        const origin = request.headers.get("Origin");
        if (origin && entries.includes(origin)) {
            response.headers.set("Access-Control-Allow-Origin", origin);
            response.headers.set("Vary", "Origin");
        }
    }
    response.headers.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
    response.headers.set("Access-Control-Allow-Headers", ALLOWED_HEADERS);
    response.headers.set("Access-Control-Expose-Headers", EXPOSED_HEADERS);
}

export function preflightResponse(request: Request, options: CorsOptions): Response {
    const response = new Response(null, { status: 204 });
    applyCors(request, response, options);
    return response;
}
