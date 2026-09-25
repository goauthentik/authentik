import {
    MaxDiffPixelRatio,
    ViewportSize,
    VisualEnvironment,
    VisualReportDirectory,
} from "./test/visual/environment.ts";

import { defineConfig, devices } from "@playwright/test";

const { baselineDirectory, storybookDirectory, storybookPort, pageURL } = VisualEnvironment;

const storybookURL = `http://127.0.0.1:${storybookPort}`;

const screenshotDefaults = {
    animations: "disabled",
    caret: "hide",
    scale: "css",
} as const;

export default defineConfig({
    testDir: "./test/visual",
    testMatch: /\.visual\.ts$/,
    snapshotPathTemplate: `${baselineDirectory}/{projectName}/{arg}{ext}`,
    outputDir: "./test-results/visual",
    fullyParallel: true,
    workers: "50%",
    reporter: [["list"], ["html", { open: "never", outputFolder: VisualReportDirectory }]],
    use: {
        ...devices["Desktop Chrome"],
        viewport: ViewportSize.Desktop,
        deviceScaleFactor: 1,
        locale: "en-US",
        timezoneId: "UTC",
        testIdAttribute: "data-test-id",
    },
    projects: [
        {
            name: "storybook",
            testMatch: /stories\.visual\.ts$/,
            use: { baseURL: storybookURL },
            expect: {
                toHaveScreenshot: {
                    ...screenshotDefaults,
                    maxDiffPixelRatio: MaxDiffPixelRatio.Storybook,
                },
            },
        },
        {
            name: "pages",
            testMatch: /pages\.visual\.ts$/,
            use: { baseURL: pageURL },
            timeout: 60_000,
            expect: {
                toHaveScreenshot: {
                    ...screenshotDefaults,
                    maxDiffPixelRatio: MaxDiffPixelRatio.Pages,
                },
            },
        },
    ],
    webServer: {
        command: "node test/visual/serve.ts",
        url: `${storybookURL}/index.json`,
        env: {
            AK_VISUAL_STORYBOOK_DIR: storybookDirectory,
            AK_VISUAL_STORYBOOK_PORT: String(storybookPort),
        },
        reuseExistingServer: false,
        stdout: "ignore",
    },
});
