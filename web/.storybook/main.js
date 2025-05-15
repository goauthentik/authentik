/**
 * @file Storybook configuration.
 * @import { StorybookConfig } from "@storybook/web-components-vite";
 * @import { InlineConfig, Plugin } from "vite";
 */
import { cwd } from "process";
import postcssLit from "rollup-plugin-postcss-lit";
import tsconfigPaths from "vite-tsconfig-paths";

const NODE_ENV = process.env.NODE_ENV || "development";

const CSSImportPattern = /import [\w\$]+ from .+\.(css)/g;
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
    viteFinal({ plugins = [], ...config }) {
        /**
         * @satisfies {InlineConfig}
         */
        const mergedConfig = {
            ...config,
            define: {
                "process.env.NODE_ENV": JSON.stringify(NODE_ENV),
                "process.env.CWD": JSON.stringify(cwd()),
                "process.env.AK_API_BASE_PATH": JSON.stringify(process.env.AK_API_BASE_PATH || ""),
            },
            plugins: [inlineCSSPlugin, ...plugins, postcssLit(), tsconfigPaths()],
        };

        return mergedConfig;
    },
};

export default config;
