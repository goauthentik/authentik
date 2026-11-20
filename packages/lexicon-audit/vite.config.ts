import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        name: "Lexicon audit",
        environment: "node",
        include: ["test/*.test.ts"],
        typecheck: { tsconfig: "./test/tsconfig.json" },
    },
});
