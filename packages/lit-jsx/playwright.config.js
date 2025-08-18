/**
 * @file Playwright configuration.
 *
 * @see https://playwright.dev/docs/test-configuration
 *
 */

import { defineConfig, devices } from "@playwright/test";

const CI = !!process.env.CI;

const baseURL = process.env.AK_TEST_RUNNER_PAGE_URL ?? "http://localhost:9000";

export default defineConfig({
    testDir: "./test/browser",
    fullyParallel: true,
    forbidOnly: CI,
    retries: CI ? 2 : 0,
    workers: CI ? 1 : undefined,
    reporter: CI
        ? "github"
        : [
              // ---
              ["list", { printSteps: true }],
              ["html", { open: "never" }],
          ],
    use: {
        testIdAttribute: "data-test-id",
        baseURL,
        trace: "on-first-retry",
    },

    /* Configure projects for major browsers */
    projects: [
        {
            name: "chromium",

            use: {
                ...devices["Desktop Chrome"],
            },
        },
    ],
});
