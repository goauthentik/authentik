/**
 * @file WebdriverIO configuration file for **component unit tests**.
 *
 * @see https://webdriver.io/docs/configurationfile.html
 */

import * as path from "node:path";

import { addCommands } from "../commands.mjs";

import { createBundleDefinitions } from "#bundler/utils/node";
import { inlineCSSPlugin } from "#bundler/vite-plugin-lit-css/node";
import { PackageRoot } from "#paths/node";

const headless = !process.env.HEADLESS || !!process.env.CI;
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
        define: createBundleDefinitions(),
        plugins: [
            // ---
            inlineCSSPlugin(),
        ],
    },
};

/**
 * @satisfies {WebdriverIO.Config}
 */
export const config = {
    runner: ["browser", browserRunnerOptions],

    tsConfigPath: path.resolve(PackageRoot, "tests", "tsconfig.test.json"),

    specs: [path.resolve(PackageRoot, "tests", "specs", "**", "*.ts")],

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
