import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        name: "Geo",
        // Pure geometry, binning and label math for the archive generator —
        // no DOM. The map element and its style live in web/.
        environment: "node",
        include: ["test/*.test.ts"],
        typecheck: { tsconfig: "./test/tsconfig.json" },
    },
});
