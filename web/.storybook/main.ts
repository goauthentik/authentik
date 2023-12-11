import replace from "@rollup/plugin-replace";
import type { StorybookConfig } from "@storybook/web-components-vite";
import { cwd } from "process";
import modify from "rollup-plugin-modify";
import postcssLit from "rollup-plugin-postcss-lit";
import tsconfigPaths from "vite-tsconfig-paths";

import { cssImportMaps } from "./css-import-maps";

export const isProdBuild = process.env.NODE_ENV === "production";
export const apiBasePath = process.env.AK_API_BASE_PATH || "";

const config: StorybookConfig = {
    stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
    addons: [
        "@storybook/addon-controls",
        "@storybook/addon-links",
        "@storybook/addon-essentials",
        "@jeysal/storybook-addon-css-user-preferences",
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
        return {
            ...config,
            plugins: [
                modify(cssImportMaps),
                replace({
                    "process.env.NODE_ENV": JSON.stringify(
                        isProdBuild ? "production" : "development",
                    ),
                    "process.env.CWD": JSON.stringify(cwd()),
                    "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
                    "preventAssignment": true,
                }),
                ...config.plugins,
                postcssLit(),
                tsconfigPaths(),
            ],
        };
    },
};

export default config;
