/// <reference types="@wdio/globals/types" />
/**
 * @file WebdriverIO configuration file
 * @see https://webdriver.io/docs/configurationfile.html
 */
import { browser } from "@wdio/globals";
import type { Options } from "@wdio/types";
import { RequestedStandaloneCapabilities } from "@wdio/types/build/Capabilities";
import { cwd } from "node:process";
import { type UserConfig, mergeConfig } from "vite";
import litCSS from "vite-plugin-lit-css";
import tsconfigPaths from "vite-tsconfig-paths";

const NODE_ENV = process.env.NODE_ENV || "development";
const AK_API_BASE_PATH = process.env.AK_API_BASE_PATH || "";

const lemmeSee = Boolean(process.env.WDIO_LEMME_SEE);

const testSafari = Boolean(process.env.WDIO_TEST_SAFARI);
const testFirefox = Boolean(process.env.WDIO_TEST_FIREFOX);
const skipChrome = Boolean(process.env.WDIO_SKIP_CHROME);
const runHeadless = Boolean(process.env.CI);

const capabilities: RequestedStandaloneCapabilities[] = [];

const DEFAULT_MAX_INSTANCES = 10;

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

const maxInstances =
    process.env.MAX_INSTANCES !== undefined
        ? parseInt(process.env.MAX_INSTANCES, DEFAULT_MAX_INSTANCES)
        : runHeadless
          ? 1
          : 1;

const runnerOptions = {
    viteConfig: (userConfig: UserConfig) => {
        const mergedConfig = mergeConfig(userConfig, {
            define: {
                "process.env.NODE_ENV": JSON.stringify(NODE_ENV),
                "process.env.CWD": JSON.stringify(cwd()),
                "process.env.AK_API_BASE_PATH": JSON.stringify(AK_API_BASE_PATH),
                "process.env.WATCHER_URL": "",
            },
            plugins: [litCSS(), tsconfigPaths()],
        });

        return mergedConfig;
    },
} satisfies WebdriverIO.BrowserRunnerOptions;

export const config: Options.Testrunner = {
    runner: ["browser", runnerOptions],

    // @ts-expect-error TS2353: The types are not up-to-date with Wdio9.
    autoCompileOpts: {
        autoCompile: true,
        tsNodeOpts: {
            project: "./tsconfig.json",
            transpileOnly: true,
        },
    },

    specs: ["./src/**/*.test.ts"],
    // Patterns to exclude.
    exclude: [
        // 'path/to/excluded/files'
    ],

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
    afterTest: async () => {
        if (lemmeSee) {
            await browser.pause(500);
        }
    },
};
