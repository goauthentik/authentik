/// <reference types="vitest/config" />

import { join } from "node:path";

import { createBundleDefinitions } from "#bundler/utils/node";
import { inlineCSSPlugin } from "#bundler/vite-plugin-lit-css/node";

import { resolvePackage } from "@goauthentik/core/paths/node";

import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vite";

const patternflyPath = resolvePackage("@patternfly/patternfly", import.meta);

export default defineConfig({
    define: createBundleDefinitions(),
    resolve: {
        alias: {
            "./assets/fonts": join(patternflyPath, "assets", "fonts"),
            "./assets/pficon": join(patternflyPath, "assets", "pficon"),
        },
    },
    optimizeDeps: {
        // Fixes dependency resolution issue associated with `npm link`ed packages.
        include: ["@goauthentik/api"],
    },
    plugins: [
        // ---
        inlineCSSPlugin(),
    ],

    test: {
        dir: "./test",
        exclude: [
            "**/node_modules/**",
            "**/dist/**",
            "**/out/**",
            "**/.{idea,git,cache,output,temp}/**",
            "**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build,eslint,prettier}.config.*",
        ],
        projects: [
            {
                // The root `tsconfig.json` excludes `src/**/*.test.ts`, so `vite:oxc`'s
                // per-file tsconfig discovery bails with `[TSCONFIG_ERROR] Tsconfig not
                // found` on co-located `src/**/*.unit.test.ts`. Disabling tsconfig
                // discovery for this Node project lets oxc transform those files while
                // leaving `lint:types` (`tsgo -p .`) and the root excludes untouched.
                // `tsconfig` is forwarded to oxc's transform at runtime but is omitted
                // from vite's `OxcOptions` type, so the assertion adds it back to keep
                // `tsgo -p .` clean.
                oxc: /** @type {import("vite").OxcOptions & { tsconfig: false }} */ ({
                    tsconfig: false,
                }),
                test: {
                    include: ["./test/unit/**/*.{test,spec}.ts", "**/*.unit.{test,spec}.ts"],
                    name: "Unit Tests",
                    environment: "node",
                    typecheck: {
                        tsconfig: "./tsconfig.unit.json",
                    },
                },
            },
            {
                plugins: [inlineCSSPlugin()],
                test: {
                    setupFiles: ["./test/lit/setup.js"],

                    include: ["./browser/**/*.{test,spec}.ts", "**/*.browser.{test,spec}.ts"],
                    name: "Browser Tests",
                    browser: {
                        enabled: true,
                        provider: playwright(),

                        instances: [
                            {
                                browser: "chromium",
                            },
                        ],
                    },
                },
            },
        ],
    },
});
