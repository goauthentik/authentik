import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        name: "dev-mcp",
        environment: "node",
        include: ["test/*.test.ts"],
    },
});
