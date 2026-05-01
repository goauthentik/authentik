/**
 * @file Playwright configuration.
 *
 * @see https://playwright.dev/docs/test-configuration
 *
 * @import { LogFn, Logger } from "pino"
 */

import { ConsoleLogger } from "#logger/node";

import { defineConfig, devices } from "@playwright/test";

const CI = !!process.env.CI;

/**
 * @type {Map<string, Logger>}
 */
const LoggerCache = new Map();

const baseURL = process.env.AK_TEST_RUNNER_PAGE_URL ?? "http://localhost:9000";

export default defineConfig({
    testDir: "./test/browser",
    fullyParallel: true,
    forbidOnly: CI,
    retries: CI ? 1 : 0,
    workers: "50%",
    maxFailures: CI ? 5 : 2,
    reporter: CI
        ? [
              // ---
              ["github"],
              ["html", { open: "never", outputFolder: "playwright-report" }],
          ]
        : [
              // ---
              ["list", { printSteps: true }],
              ["html", { open: "never" }],
          ],
    use: {
        testIdAttribute: "data-test-id",
        baseURL,
        trace: "on-first-retry",
        screenshot: "only-on-failure",
        video: CI ? "retain-on-failure" : "off",
        colorScheme: "dark",
        launchOptions: {
            logger: {
                isEnabled() {
                    return true;
                },
                log: (name, severity, message, _args) => {
                    let logger = LoggerCache.get(name);

                    if (!logger) {
                        logger = ConsoleLogger.child({
                            name: `Playwright ${name.toUpperCase()}`,
                        });
                        LoggerCache.set(name, logger);
                    }

                    /**
                     * @type {LogFn}
                     */
                    let log;

                    switch (severity) {
                        case "verbose":
                            log = logger.debug;
                            break;
                        case "warning":
                            log = logger.warn;
                            break;
                        case "error":
                            log = logger.error;
                            break;
                        default:
                            log = logger.info;
                            break;
                    }

                    if (name === "api") {
                        log = logger.debug;
                    }

                    log.call(logger, message.toString());
                },
            },
        },
    },

    /* Configure projects for major browsers */
    projects: [
        {
            name: "prerequisites",
            testMatch: /prerequisites\.setup\.ts/,
        },
        {
            name: "chromium",
            dependencies: ["prerequisites"],
            use: {
                ...devices["Desktop Chrome"],
                headless: false,
            },
        },
    ],
});
