import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        name: "dev-mcp",
        environment: "node",
        root: import.meta.dirname,
        include: ["test/*.test.ts"],
    },
});
