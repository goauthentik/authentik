/**
 * @file Playwright global teardown: merge the per-worker coverage cache into
 * `coverage/lcov.info`.
 *
 * @see {@linkcode file://./coverage.ts}
 */

import { COVERAGE_ENABLED, createCoverageReport } from "#e2e/coverage";

export default async function coverageTeardown(): Promise<void> {
    if (!COVERAGE_ENABLED) return;

    const report = createCoverageReport();

    await report.generate();
    // ponytail: no globalSetup counterpart — the cache is cleaned on the way out
    // instead of on the way in, so a run killed before teardown leaves a stale
    // cache that inflates the next local report. CI checkouts start empty.
    await report.cleanCache();
}
