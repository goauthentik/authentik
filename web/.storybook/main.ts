import path from "path";
import tsconfigPaths from "vite-tsconfig-paths";
import replace from "@rollup/plugin-replace";
import { cwd } from "process";
import type { StorybookConfig } from "@storybook/web-components-vite";
import postcssLit from "rollup-plugin-postcss-lit";

export const isProdBuild = process.env.NODE_ENV === "production";
export const apiBasePath = process.env.AK_API_BASE_PATH || "";

const config: StorybookConfig = {
    stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
    addons: ["@storybook/addon-links", "@storybook/addon-essentials", "@jeysal/storybook-addon-css-user-preferences"],
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
                ...config.plugins,
                postcssLit(),
                tsconfigPaths(),
                replace({
                    "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
                    "process.env.CWD": JSON.stringify(cwd()),
                    "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
                    "preventAssignment": true,
                }),
            ],
        };
    },
};

export default config;
