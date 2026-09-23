/**
 * @file Static server for a built Storybook.
 * @runtime node
 */

import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, sep } from "node:path";

import { VisualEnvironment } from "./environment.ts";

const { storybookDirectory: root, storybookPort: port } = VisualEnvironment;

const ContentTypes: Record<string, string> = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
};

function resolveFile(pathname: string): string | null {
    const candidate = join(root, normalize(decodeURIComponent(pathname)));

    if (candidate !== root && !candidate.startsWith(root + sep)) return null;

    try {
        const stats = statSync(candidate);

        return stats.isDirectory() ? resolveFile(join(pathname, "index.html")) : candidate;
    } catch {
        return null;
    }
}

createServer((req, res) => {
    const { pathname } = new URL(req.url ?? "/", "http://localhost");
    const filePath = resolveFile(pathname);

    if (!filePath) {
        res.writeHead(404).end();

        return;
    }

    res.writeHead(200, {
        "content-type": ContentTypes[extname(filePath)] ?? "application/octet-stream",
    });

    createReadStream(filePath).pipe(res);
}).listen(port, "127.0.0.1", () => {
    console.log(`Serving ${root} at http://127.0.0.1:${port}`);
});
