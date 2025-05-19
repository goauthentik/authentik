/**
 * @file Storybook configuration.
 * @import { StorybookConfig } from "@storybook/web-components-vite";
 * @import { InlineConfig, Plugin } from "vite";
 */
import postcssLit from "rollup-plugin-postcss-lit";
import { mergeConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

import { createBundleDefinitions } from "../bundler/utils/node.js";

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
    viteFinal(config) {
        /**
         * @satisfies {InlineConfig}
         */
        const overrides = {
            define: createBundleDefinitions(),
            plugins: [inlineCSSPlugin, postcssLit(), tsconfigPaths()],
        };

        return mergeConfig(config, overrides);
    },
};
export default config;
