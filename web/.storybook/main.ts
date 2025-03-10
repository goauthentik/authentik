import replace from "@rollup/plugin-replace";
import type { StorybookConfig } from "@storybook/web-components-vite";
import { cwd } from "process";
import modify from "rollup-plugin-modify";
import postcssLit from "rollup-plugin-postcss-lit";
import tsconfigPaths from "vite-tsconfig-paths";

export const isProdBuild = process.env.NODE_ENV === "production";
export const apiBasePath = process.env.AK_API_BASE_PATH || "";

const importInlinePatterns = [
    'import AKGlobal from "(\\.\\./)*common/styles/authentik\\.css',
    'import AKGlobal from "@goauthentik/common/styles/authentik\\.css',
    'import PF.+ from "@patternfly/patternfly/\\S+\\.css',
    'import ThemeDark from "@goauthentik/common/styles/theme-dark\\.css',
    'import styles from "\\./LibraryPageImpl\\.css',
];

const importInlineRegexp = new RegExp(importInlinePatterns.map((a) => `(${a})`).join("|"));

const config: StorybookConfig = {
    stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
    addons: [
        "@storybook/addon-controls",
        "@storybook/addon-links",
        "@storybook/addon-essentials",
        "storybook-addon-mock",
    ],
    staticDirs: [
        {
            from: "../node_modules/@patternfly/patternfly/patternfly-base.css",
            to: "@patternfly/patternfly/patternfly-base.css",
        },
        {
            from: "../src/common/styles/authentik.css",
            to: "@goauthentik/common/styles/authentik.css",
        },
        {
            from: "../src/common/styles/theme-dark.css",
            to: "@goauthentik/common/styles/theme-dark.css",
        },
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
                modify({
                    find: importInlineRegexp,
                    replace: (match: RegExpMatchArray) => {
                        return `${match}?inline`;
                    },
                }),
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
