import { isCoveredSource, toRepoPath } from "#e2e/coverage";

import { describe, expect, it } from "vitest";

// What the resolver hands the report for a bundle served from
// /static/dist/admin/, whose sourcemap points at `../../<path>`.
const resolved = (path: string) => `/home/runner/work/authentik/${path}`;

describe("coverage source paths", () => {
    it("rewrites app sources to their path in the repo", () => {
        expect(toRepoPath(resolved("src/elements/banner/Banner.ts"))).toBe(
            "web/src/elements/banner/Banner.ts",
        );
    });

    it("keeps the root a dependency or workspace package is under", () => {
        expect(toRepoPath(resolved("node_modules/lit/src/lit-element.ts"))).toBe(
            "web/node_modules/lit/src/lit-element.ts",
        );
        expect(toRepoPath(resolved("packages/logger-js/src/index.ts"))).toBe(
            "web/packages/logger-js/src/index.ts",
        );
    });

    it("covers only the app's own sources", () => {
        expect(isCoveredSource("web/src/elements/banner/Banner.ts")).toBe(true);
        expect(isCoveredSource("web/node_modules/lit/src/lit-element.ts")).toBe(false);
        expect(isCoveredSource("web/packages/logger-js/src/index.ts")).toBe(false);
    });
});
