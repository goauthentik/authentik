/**
 * @file WebdriverIO configuration file for **integration tests**.
 *
 * @see https://webdriver.io/docs/configurationfile.html
 */
import { browser } from "@wdio/globals";

import { addCommands } from "./commands.mjs";

/// <reference types="@wdio/globals/types" />
/// <reference types="./types/webdriver.js" />

const headless = !!process.env.CI;
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
        "./tests/specs/new-application-by-wizard.ts",
    ],
    exclude: [],
    maxInstances: 1,
    capabilities,

    logLevel: "warn",
    baseUrl: "http://localhost",
    waitforTimeout: 10000,
    connectionRetryTimeout: 120000,
    connectionRetryCount: 3,

    framework: "mocha",
    reporters: ["spec"],
    mochaOpts: {
        ui: "bdd",
        timeout: 60000,
    },
    /**
     * @param {WebdriverIO.Capabilities} capabilities
     * @param {string[]} specs
     * @param {WebdriverIO.Browser} browser
     * @returns {void}
     */
    before(capabilities, specs, browser) {
        addCommands(browser);
    },

    afterTest() {
        if (lemmeSee) return browser.pause(500);
    },
};
