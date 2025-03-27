import type { StorybookConfig } from "@storybook/web-components-vite";
import { cwd } from "node:process";
import modify from "rollup-plugin-modify";
import postcssLit from "rollup-plugin-postcss-lit";
import { mergeConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export const isProdBuild = process.env.NODE_ENV === "production";
export const apiBasePath = process.env.AK_API_BASE_PATH || "";

const NODE_ENV = process.env.NODE_ENV || "development";
const AK_API_BASE_PATH = process.env.AK_API_BASE_PATH || "";

const importInlinePatterns = [
    'import AKGlobal from "(\\.\\./)*common/styles/authentik\\.css',
    'import AKGlobal from "@goauthentik/common/styles/authentik\\.css',
    'import PF.+ from "@patternfly/patternfly/\\S+\\.css',
    'import ThemeDark from "@goauthentik/common/styles/theme-dark\\.css',
    'import OneDark from "@goauthentik/common/styles/one-dark\\.css',
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
        {
            from: "../src/common/styles/one-dark.css",
            to: "@goauthentik/common/styles/one-dark.css",
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
        return mergeConfig(config, {
            define: {
                "process.env.NODE_ENV": JSON.stringify(NODE_ENV),
                "process.env.CWD": JSON.stringify(cwd()),
                "process.env.AK_API_BASE_PATH": JSON.stringify(AK_API_BASE_PATH),
                "process.env.WATCHER_URL": "",
            },

            plugins: [
                modify({
                    find: importInlineRegexp,
                    replace: (match: RegExpMatchArray) => {
                        return `${match}?inline`;
                    },
                }),
                postcssLit(),
                tsconfigPaths(),
            ],
        });
    },
};

export default config;
