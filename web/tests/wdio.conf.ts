/// <reference types="@wdio/globals/types" />
/**
 * @file WebdriverIO configuration file
 * @see https://webdriver.io/docs/configurationfile.html
 */
import { browser } from "@wdio/globals";
import { RequestedStandaloneCapabilities } from "@wdio/types/build/Capabilities";

const lemmeSee = Boolean(process.env.WDIO_LEMME_SEE);

const testSafari = Boolean(process.env.WDIO_TEST_SAFARI);
const testFirefox = Boolean(process.env.WDIO_TEST_FIREFOX);
const skipChrome = Boolean(process.env.WDIO_SKIP_CHROME);
const runHeadless = Boolean(process.env.CI);

const capabilities: RequestedStandaloneCapabilities[] = [];

if (!skipChrome) {
    const chromeBrowserConfig = {
        "browserName": "chrome",
        "wdio:chromedriverOptions": {
            binary: "./node_modules/.bin/chromedriver",
        },
        "goog:chromeOptions": {
            args: ["disable-infobars", "window-size=1280,800"],
        },
    } satisfies RequestedStandaloneCapabilities;

    if (runHeadless) {
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

if (testSafari) {
    capabilities.push({
        browserName: "safari",
    });
}

if (testFirefox) {
    capabilities.push({
        browserName: "firefox",
    });
}

export const config: WebdriverIO.Config = {
    runner: "local",
    tsConfigPath: "./tsconfig.json",

    specs: ["./specs/**/*.ts"],
    exclude: [
        // 'path/to/excluded/files'
    ],
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
    afterTest: async () => {
        if (lemmeSee) {
            await browser.pause(500);
        }
    },
};
