/// <reference types="vitest/config" />

import { defineConfig } from "vite";

export default defineConfig({
    test: {
        name: "unit",
        environment: "node",
        dir: "./test",
        include: ["./**/*.test.{ts,tsx}"],
    },
});
