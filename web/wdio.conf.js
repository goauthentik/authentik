/**
 * @file WebdriverIO configuration file for **integration tests**.
 *
 * @see https://webdriver.io/docs/configurationfile.html
 */
import { PackageRoot } from "#paths/node";
import { addCommands } from "#tests/commands";

/**
 * Common browser runner options.
 *
 * @category WebdriverIO
 *
 * @satisfies {WebdriverIO.BrowserRunnerOptions}
 */
const browserRunnerOptions = {
    headless: !!process.env.CI || !!process.env.WDIO_HEADLESS,
    preset: "lit",
    rootDir: PackageRoot,
};

/**
 * @satisfies {WebdriverIO.Config}
 */
export const config = {
    runner: ["browser", browserRunnerOptions],
    tsConfigPath: "./tsconfig.json",
    specs: [
        // "./tests/specs/**/*.ts"
        "./tests/specs/sessions.ts",
        // "./tests/specs/oauth-provider.ts",
        // "./tests/specs/providers.ts",
        // "./tests/specs/new-application-by-wizard.ts",
    ],
    maxInstances: 1,

    capabilities: [
        {
            "browserName": "chrome",
            "goog:chromeOptions": {
                prefs: {
                    "profile.password_manager_leak_detection": false,
                },
                args: [
                    "remote-debugging-port=9222",

                    // ---
                    "disable-infobars",
                    "no-sandbox",
                    "browser-test",
                    "disable-dev-shm-usage",
                    "window-position=0,0",
                    "window-size=1280,800",
                ],
            },
        },
    ],

    bail: 0,
    // injectGlobals: false,
    // logLevel: "error",
    logLevel: "trace",
    // baseUrl: "http://localhost",
    waitforInterval: 500,
    waitforTimeout: 10_000,
    connectionRetryTimeout: 120000,
    connectionRetryCount: 3,

    // connectionRetryTimeout: 120_000,
    // connectionRetryCount: 3,

    framework: "mocha",
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
        // ConsoleTestRunner.setLevel("info");
        addCommands(browser);
    },

    // afterTest() {
    //     if (lemmeSee) return browser.pause(500);
    // },
};
