import { fileURLToPath } from "node:url";

import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vitest/config";

const src = (path: string) => fileURLToPath(new URL(`./src/${path}`, import.meta.url));

export default defineConfig({
    resolve: {
        // Mirror tsconfig.test.json "paths": tests exercise the real package
        // specifiers without requiring a dist/ build first.
        alias: {
            "@goauthentik/lit-jsx/jsx-runtime": src("jsx-runtime.ts"),
            "@goauthentik/lit-jsx/jsx-dev-runtime": src("jsx-dev-runtime.ts"),
            "@goauthentik/lit-jsx": src("index.ts"),
        },
    },
    // Vite 8 transforms TS/JSX with oxc (rolldown-based), not esbuild. The
    // `esbuild` option is only honored when `oxc` is unset, so the JSX
    // runtime/import source must be configured here instead.
    oxc: {
        jsx: {
            runtime: "automatic",
            importSource: "@goauthentik/lit-jsx",
        },
    },
    test: {
        projects: [
            {
                extends: true,
                test: {
                    name: "unit",
                    environment: "node",
                    include: ["test/unit/**/*.test.{ts,tsx}"],
                },
            },
            {
                extends: true,
                test: {
                    name: "browser",
                    include: ["test/browser/**/*.browser.test.{ts,tsx}"],
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
