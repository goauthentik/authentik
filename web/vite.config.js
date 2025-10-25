/// <reference types="vitest/config" />

import { createBundleDefinitions } from "#bundler/utils/node";
import { inlineCSSPlugin } from "#bundler/vite-plugin-lit-css/node";

import { defineConfig } from "vite";

export default defineConfig({
    define: createBundleDefinitions(),
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
                        provider: "playwright",

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
