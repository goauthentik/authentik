/**
 * @file Storybook configuration.
 * @import { StorybookConfig } from "@storybook/web-components-vite";
 */

import { dirname, join } from "node:path";

const relativePackageJSONPath = join("@patternfly/patternfly", "package.json");
const absolutePackageJSONPath = require.resolve(relativePackageJSONPath);
const patternflyPath = dirname(absolutePackageJSONPath);

/**
 * @satisfies {StorybookConfig}
 */
const config = {
    stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
    staticDirs: [
        { from: "../icons", to: "/static/dist/assets/icons" },
        {
            from: join(patternflyPath, "assets", "fonts"),
            to: "/assets/fonts",
        },
        { from: "../authentik", to: "/static/authentik" },
    ],
    addons: [
        // ---
        "@storybook/addon-links",
        "@storybook/addon-docs",
    ],
    framework: "@storybook/web-components-vite",
};

export default config;
