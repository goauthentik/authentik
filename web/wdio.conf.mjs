/**
 * @file WebdriverIO configuration file for **integration tests**.
 *
 * @see https://webdriver.io/docs/configurationfile.html
 */
import { addCommands } from "#tests/commands";
import { ConsoleTestRunner } from "#tests/utils/logger";
import { browser } from "@wdio/globals";

const headless = !!process.env.CI || !!process.env.WDIO_HEADLESS;
const lemmeSee = !!process.env.WDIO_LEMME_SEE;

/**
 * @type {WebdriverIO.Capabilities[]}
 */
const capabilities = [];

if (!process.env.WDIO_SKIP_CHROME) {
    /**
     * @satisfies {WebdriverIO.Capabilities}
     */
    const chromeBrowserConfig = {
        "browserName": "chrome",
        // "wdio:chromedriverOptions": {
        //     binary: "./node_modules/.bin/chromedriver",
        // },
        "goog:chromeOptions": {
            args: ["disable-infobars", "window-size=1280,800"],
        },
    };

    if (headless) {
        chromeBrowserConfig["goog:chromeOptions"].args.push(
            "headless",
            "no-sandbox",
            "disable-gpu",
            "disable-setuid-sandbox",
            "disable-dev-shm-usage",
        );
    }

    capabilities.push(chromeBrowserConfig);
}

if (process.env.WDIO_TEST_SAFARI) {
    capabilities.push({
        browserName: "safari",
    });
}

if (process.env.WDIO_TEST_FIREFOX) {
    capabilities.push({
        browserName: "firefox",
    });
}

/**
 * @satisfies {WebdriverIO.Config}
 */
export const config = {
    runner: "local",
    tsConfigPath: "./tsconfig.json",
    specs: [
        // "./tests/specs/**/*.ts"
        // "./tests/specs/sessions.ts",
        "./tests/specs/oauth-provider.ts",
        // "./tests/specs/providers.ts",
        // "./tests/specs/new-application-by-wizard.ts",
    ],
    exclude: [],
    maxInstances: 1,
    capabilities,

    logLevel: "error",
    baseUrl: "http://localhost",
    waitforInterval: 800,
    waitforTimeout: 10_000,
    // connectionRetryTimeout: 120_000,
    // connectionRetryCount: 3,

    // framework: "mocha",
    reporters: ["spec"],
    mochaOpts: {
        ui: "bdd",
        timeout: 15_000,
        // timeout: 10_000,
    },
    /**
     * @param {WebdriverIO.Browser} browser
     */
    before(_capabilities, _specs, browser) {
        ConsoleTestRunner.setLevel("info");
        addCommands(browser);
    },

    afterTest() {
        if (lemmeSee) return browser.pause(500);
    },
};
