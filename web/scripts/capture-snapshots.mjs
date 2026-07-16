#!/usr/bin/env node
/**
 * @file Captures a PNG screenshot of every Storybook story for upload to Sentry Snapshots.
 *
 * Expects `storybook-static/` to already exist (`pnpm run storybook:build`).
 * Output goes to `snapshots/<title-path>/<story-name>.png`, grouped by the
 * story's `title` (e.g. "Elements/ak-alert" -> snapshots/Elements/ak-alert/<story>.png).
 */

import { createReadStream } from "node:fs";
import { mkdir, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const STATIC_DIR = join(ROOT, "storybook-static");
const OUTPUT_DIR = join(ROOT, "snapshots");

/**
 * @type {Record<string, string>}
 */
const MIME_TYPES = {
    ".html": "text/html",
    ".js": "text/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
};

/**
 * @param {string} root
 */
function serveStatic(root) {
    const server = createServer(async (req, res) => {
        const url = new URL(req.url ?? "/", "http://localhost");
        let path = join(root, decodeURIComponent(url.pathname));

        try {
            const info = await stat(path);
            if (info.isDirectory()) {
                path = join(path, "index.html");
                await stat(path);
            }
        } catch {
            res.writeHead(404);
            res.end();
            return;
        }

        res.writeHead(200, {
            "Content-Type": MIME_TYPES[extname(path)] ?? "application/octet-stream",
        });
        createReadStream(path).pipe(res);
    });
    return new Promise((resolve) => {
        server.listen(0, "127.0.0.1", () => resolve(server));
    });
}

/**
 * @param {string} segment
 */
function sanitize(segment) {
    return segment.replace(/[^a-zA-Z0-9._-]+/g, "-");
}

async function main() {
    const server = await serveStatic(STATIC_DIR);
    const { port } = server.address();
    const baseUrl = `http://127.0.0.1:${port}`;

    try {
        const index = await fetch(`${baseUrl}/index.json`).then((res) => res.json());
        const stories = Object.values(index.entries ?? index.stories ?? {}).filter(
            (entry) => entry.type === "story",
        );

        await mkdir(OUTPUT_DIR, { recursive: true });

        const browser = await chromium.launch();
        try {
            const page = await browser.newPage();
            for (const story of stories) {
                const groupPath = story.title.split("/").map(sanitize).join("/");
                const dir = join(OUTPUT_DIR, groupPath);
                await mkdir(dir, { recursive: true });

                try {
                    await page.goto(`${baseUrl}/iframe.html?id=${story.id}&viewMode=story`, {
                        waitUntil: "networkidle",
                    });
                    await page.screenshot({ path: join(dir, `${sanitize(story.name)}.png`) });

                    console.log(`Captured ${story.title}/${story.name}`);
                } catch (error) {
                    console.warn(`Skipping ${story.title}/${story.name}: ${error}`);
                }
            }
        } finally {
            await browser.close();
        }
    } finally {
        server.close();
    }
}

await main();
