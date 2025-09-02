/**
 * @file WebdriverIO configuration file for **integration tests**.
 *
 * @see https://webdriver.io/docs/configurationfile.html
 */

import * as path from "node:path";

import { addCommands } from "./commands.mjs";

import { createBundleDefinitions } from "#bundler/utils/node";
import { inlineCSSPlugin } from "#bundler/vite-plugin-lit-css/node";
import { PackageRoot } from "#paths/node";

import { browser } from "@wdio/globals";

/// <reference types="@wdio/globals/types" />
/// <reference types="./types/webdriver.js" />

const headless = !process.env.HEADLESS || !!process.env.CI;
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

    tsConfigPath: path.resolve(PackageRoot, "tsconfig.test.json"),

    specs: [path.resolve(PackageRoot, "src", "**", "*.test.ts")],

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
     * @param {WebdriverIO.Browser} browser
     */
    before(_capabilities, _specs, browser) {
        addCommands(browser);
    },

    afterTest() {
        if (lemmeSee) return browser.pause(500);
    },
};
