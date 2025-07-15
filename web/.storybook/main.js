/**
 * @file Storybook configuration.
 * @import { StorybookConfig } from "@storybook/web-components-vite";
 * @import { InlineConfig, Plugin } from "vite";
 */

import postcssLit from "rollup-plugin-postcss-lit";

const CSSImportPattern = /import [\w$]+ from .+\.(css)/g;
const JavaScriptFilePattern = /\.m?(js|ts|tsx)$/;

/**
 * @satisfies {Plugin<never>}
 */
const inlineCSSPlugin = {
    name: "inline-css-plugin",
    transform: (source, id) => {
        if (!JavaScriptFilePattern.test(id)) return;

        const code = source.replace(CSSImportPattern, (match) => {
            return `${match}?inline`;
        });

        return {
            code,
        };
    },
};

/**
 * @satisfies {InlineConfig}
 */
// const viteFinal = ;

/**
 * @satisfies {StorybookConfig}
 */
const config = {
    stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
    staticDirs: [
        { from: "../icons", to: "/static/dist/assets/icons" },
        { from: "../authentik", to: "/static/authentik" },
    ],
    addons: [
        "@storybook/addon-controls",
        "@storybook/addon-links",
        "@storybook/addon-essentials",
        "storybook-addon-mock",
    ],
    framework: {
        name: "@storybook/web-components-vite",
        options: {},
    },
    docs: {
        autodocs: "tag",
    },
    async viteFinal(config) {
        const [{ mergeConfig }, { createBundleDefinitions }] = await Promise.all([
            import("vite"),
            import("@goauthentik/web/bundler/utils/node"),
        ]);

        /**
         * @satisfies {InlineConfig}
         */
        const overrides = {
            define: createBundleDefinitions(),
            plugins: [inlineCSSPlugin, postcssLit()],
        };

        return mergeConfig(config, overrides);
    },
};
export default config;
