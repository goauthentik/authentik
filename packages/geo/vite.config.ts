/// <reference types="vitest/config" />

import { playwright } from "@vitest/browser-playwright";
import { defineConfig, type Plugin } from "vite";

const CSSImportPattern = /import [\w$]+ from .+\.(css)/g;
const JavaScriptFilePattern = /\.m?(js|ts|tsx)$/;

/**
 * `ak-map` imports its stylesheet as text and hands it to `unsafeCSS` — the web
 * build does that with esbuild's `.css: "text"` loader. Vite injects CSS as a
 * side effect instead, so rewrite those imports to `?inline` to get the source
 * back as the default export. Mirrors web's `inlineCSSPlugin`.
 */
function inlineCSSPlugin(): Plugin {
    return {
        name: "inline-css-plugin",
        transform: (source, id) =>
            JavaScriptFilePattern.test(id)
                ? { code: source.replace(CSSImportPattern, (match) => `${match}?inline`) }
                : null,
    };
}

export default defineConfig({
    plugins: [inlineCSSPlugin()],
    // Pre-bundled up front; discovering these mid-run makes Vite reload the
    // page under the browser project, which Vitest flags as flaky.
    optimizeDeps: {
        include: [
            "@protomaps/basemaps",
            "h3-js",
            "lit",
            "lit/decorators.js",
            "maplibre-gl",
            "pmtiles",
        ],
    },
    test: {
        projects: [
            {
                test: {
                    name: "Geo",
                    // Pure geometry, binning and style-spec math — no DOM.
                    environment: "node",
                    include: ["test/*.test.ts"],
                    typecheck: { tsconfig: "./test/tsconfig.json" },
                },
            },
            {
                plugins: [inlineCSSPlugin()],
                test: {
                    name: "Geo Browser",
                    // `ak-map` drives MapLibre, which needs a real canvas.
                    include: ["test/browser/*.browser.test.ts"],
                    browser: {
                        enabled: true,
                        headless: true,
                        provider: playwright(),
                        instances: [{ browser: "chromium" }],
                    },
                },
            },
        ],
    },
});
