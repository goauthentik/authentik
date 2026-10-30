/// <reference types="vitest/config" />

import { join } from "node:path";

import { createBundleAliases, createBundleDefinitions } from "#bundler/utils/node";
import { inlineCSSPlugin } from "#bundler/vite-plugin-lit-css/node";

import { resolvePackage } from "@goauthentik/core/paths/node";

import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vite";

const patternflyPath = resolvePackage("@patternfly/patternfly", import.meta);

/**
 * @satisfies {import("vite").UserConfig["resolve"]}
 */
const resolve = {
    alias: [
        // `inlineCSSPlugin` appends `?inline` to CSS imports, which a string alias won't match.
        ...Object.entries(createBundleAliases()).map(([find, replacement]) => ({
            find: new RegExp(`^${RegExp.escape(find)}(?=\\?|$)`),
            replacement,
        })),
        { find: "./assets/fonts", replacement: join(patternflyPath, "assets", "fonts") },
        { find: "./assets/pficon", replacement: join(patternflyPath, "assets", "pficon") },
    ],
};

export default defineConfig({
    define: createBundleDefinitions(),
    resolve,
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
                // leaving `build:types` (`tsgo -p .`) and the root excludes untouched.
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
                // Projects do not inherit the root plugin list, and elements
                // import their stylesheets as text for `unsafeCSS`. Without
                // this the CSS resolves to a Vite style side-effect with no
                // default export, and importing any AKElement throws.
                plugins: [inlineCSSPlugin()],
                // Nor the root aliases, which the code editor needs for Monaco's stylesheet.
                resolve,
                test: {
                    setupFiles: ["./test/lit/setup.js"],

                    include: ["./browser/**/*.{test,spec}.ts", "**/*.browser.{test,spec}.ts"],
                    name: "Browser Tests",
                    browser: {
                        enabled: true,
                        headless: true,
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
