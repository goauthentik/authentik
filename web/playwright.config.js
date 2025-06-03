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
        baseURL: "http://localhost:9000",
        trace: "on-first-retry",
        launchOptions: {
            logger: {
                isEnabled(name, severity) {
                    return true;
                },
                log: (name, severity, message, args) => {
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

                    log.call(logger, message.toString(), args);
                },
            },
        },
    },

    /* Configure projects for major browsers */
    projects: [
        {
            name: "chromium",

            use: {
                ...devices["Desktop Chrome"],
            },
        },

        // {
        //     name: "firefox",
        //     use: { ...devices["Desktop Firefox"] },
        // },

        // {
        //     name: "webkit",
        //     use: { ...devices["Desktop Safari"] },
        // },

        /* Test against mobile viewports. */
        // {
        //   name: 'Mobile Chrome',
        //   use: { ...devices['Pixel 5'] },
        // },
        // {
        //   name: 'Mobile Safari',
        //   use: { ...devices['iPhone 12'] },
        // },

        /* Test against branded browsers. */
        // {
        //   name: 'Microsoft Edge',
        //   use: { ...devices['Desktop Edge'], channel: 'msedge' },
        // },
        // {
        //   name: 'Google Chrome',
        //   use: { ...devices['Desktop Chrome'], channel: 'chrome' },
        // },
    ],

    /* Run your local dev server before starting the tests */
    // webServer: {
    //   command: 'npm run start',
    //   url: 'http://localhost:3000',
    //   reuseExistingServer: !process.env.CI,
    // },
});
