/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import litCSS from "vite-plugin-lit-css";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
    plugins: [
        // ---
        litCSS(),
        tsconfigPaths(),
    ],
    test: {
        dir: "./test",
        exclude: [
            "**/node_modules/**",
            "**/dist/**",
            "**/out/**",
            "**/examples/**",
            "**/cypress/**",
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
