/**
 * @file V8 coverage collection for the browser suite.
 *
 * Playwright has no coverage reporter of its own, so Chromium's CDP coverage is
 * started and stopped per page by an auto fixture (`#e2e`), cached per worker by
 * monocart, and merged into `coverage/lcov.info` by the global teardown
 * (`coverage.teardown.ts`).
 */

import type { Page } from "@playwright/test";
import { CoverageReport } from "monocart-coverage-reports";

/**
 * Coverage costs a CDP round trip per page and only CI consumes the report, so
 * it stays off unless asked for.
 */
export const COVERAGE_ENABLED = !!process.env.AK_TEST_COVERAGE;

/**
 * Bundle-relative sourcemap paths (`../../src/elements/Foo.ts`) are resolved
 * against the cwd rather than against the bundle they came from, so they arrive
 * as absolute paths a couple of directories too shallow. Cut back to the first
 * directory the web workspace is rooted at: codecov matches lcov paths against
 * the repo, which knows these files as `web/src/…`.
 *
 * ponytail: a checkout path that itself contains `src/` or `packages/` cuts
 * early and mislabels the report. CI checkouts don't; fix by passing the
 * workspace root in if a dev setup trips over it.
 */
export function toRepoPath(filePath: string): string {
    return filePath.replace(/^.*?(?=(?:src|packages|node_modules)\/)/, "web/");
}

/**
 * Applied after {@linkcode toRepoPath}, on the rewritten path. Dependencies, the
 * generated API client, and the workspace packages all ride along in the bundle
 * and aren't what this suite measures.
 */
export function isCoveredSource(sourcePath: unknown): boolean {
    return typeof sourcePath === "string" && sourcePath.startsWith("web/src/");
}

/**
 * Every process that touches the coverage cache — each test worker adding to it,
 * the teardown generating from it — has to agree on where it lives and what it
 * contains.
 */
export function createCoverageReport() {
    return new CoverageReport({
        name: "authentik Web (e2e)",
        outputDir: "./coverage",
        reports: ["lcovonly", "console-summary"],

        // Everything else the page pulls in (the loading shim, third-party
        // scripts) has no sources of ours behind it.
        entryFilter: (entry) => entry.url.includes("/static/dist/"),

        sourcePath: toRepoPath,
        sourceFilter: isCoveredSource,
    });
}

/**
 * Stop coverage on a page and hand it to the worker's cache. Called once per
 * test, after the test body has run.
 */
export async function collectPageCoverage(page: Page): Promise<void> {
    // A test that crashed the page (or closed it itself) has nothing left to
    // read; losing that page's coverage beats failing an otherwise green test.
    if (page.isClosed()) return;

    await createCoverageReport().add(await page.coverage.stopJSCoverage());
}
