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
                test: {
                    include: ["./unit/**/*.{test,spec}.ts", "**/*.unit.{test,spec}.ts"],
                    name: "unit",
                    environment: "node",
                },
            },
            {
                test: {
                    setupFiles: ["./test/lit/setup.js"],

                    include: ["./browser/**/*.{test,spec}.ts", "**/*.browser.{test,spec}.ts"],
                    name: "browser",
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
