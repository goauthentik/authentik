/**
 * @file WebdriverIO configuration file for **component unit tests**.
 *
 * @see https://webdriver.io/docs/configurationfile.html
 */

import { cwd } from "node:process";

import { addCommands } from "../commands.mjs";

import litCSS from "#bundler/vite-plugin-lit-css/node";

const NODE_ENV = process.env.NODE_ENV || "development";
const headless = !!process.env.HEADLESS || !!process.env.CI;
const lemmeSee = !!process.env.WDIO_LEMME_SEE;

/**
 * @type {WebdriverIO.Capabilities[]}
 */
const capabilities = [];

const DEFAULT_MAX_INSTANCES = 10;

let maxInstances = 1;

if (headless) {
    maxInstances = process.env.MAX_INSTANCES
        ? parseInt(process.env.MAX_INSTANCES, 10)
        : DEFAULT_MAX_INSTANCES;
}

if (!process.env.WDIO_SKIP_CHROME) {
    /**
     * @satisfies {WebdriverIO.Capabilities}
     */
    const chromeBrowserConfig = {
        "browserName": "chrome",
        "goog:chromeOptions": {
            args: ["disable-search-engine-choice-screen"],
        },
    };

    if (headless) {
        chromeBrowserConfig["goog:chromeOptions"].args.push(
            "headless",
            "disable-gpu",
            "no-sandbox",
            "window-size=1280,672",
            "browser-test",
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
 * @type {WebdriverIO.BrowserRunnerOptions}
 */
const browserRunnerOptions = {
    viteConfig: {
        define: {
            "process.env.NODE_ENV": JSON.stringify(NODE_ENV),
            "process.env.CWD": JSON.stringify(cwd()),
            "process.env.AK_API_BASE_PATH": JSON.stringify(process.env.AK_API_BASE_PATH || ""),
        },
        plugins: [
            // ---
            // @ts-ignore WDIO's Vite is out of date.
            litCSS(),
        ],
    },
};
/**
 * @satisfies {WebdriverIO.Config}
 */
export const config = {
    runner: ["browser", browserRunnerOptions],

    tsConfigPath: "./tsconfig.test.json",

    specs: ["./src/**/*.test.ts"],
    exclude: [],

    maxInstances,
    capabilities,
    logLevel: "warn",
    bail: 0,
    waitforTimeout: 12000,
    connectionRetryTimeout: 12000,
    connectionRetryCount: 3,

    framework: "mocha",

    reporters: ["spec"],

    mochaOpts: {
        ui: "bdd",
        timeout: 60000,
    },
    /**
     * @param {WebdriverIO.Browser} browser
     */
    before(_capabilities, _specs, browser) {
        addCommands(browser);
    },

    afterTest() {
        if (lemmeSee) return browser.pause(500);
    },
};
