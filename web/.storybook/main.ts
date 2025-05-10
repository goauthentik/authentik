/**
 * @file Storybook configuration.
 */
import type { StorybookConfig } from "@storybook/web-components-vite";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { cwd } from "process";
import modify from "rollup-plugin-modify";
import postcssLit from "rollup-plugin-postcss-lit";
import type { InlineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

const require = createRequire(import.meta.url);

const NODE_ENV = process.env.NODE_ENV || "development";

const importInlinePatterns = [
    'import AKGlobal from "(\\.\\./)*common/styles/authentik\\.css',
    'import AKGlobal from "@goauthentik/common/styles/authentik\\.css',
    'import PF.+ from "@patternfly/patternfly/\\S+\\.css',
    'import ThemeDark from "@goauthentik/common/styles/theme-dark\\.css',
    'import OneDark from "@goauthentik/common/styles/one-dark\\.css',
    'import styles from "\\./LibraryPageImpl\\.css',
];

const importInlineRegexp = new RegExp(importInlinePatterns.map((a) => `(${a})`).join("|"));

const patternflyPackageJSONPath = require.resolve("@patternfly/patternfly/package.json");
const patternflyPackagePath = dirname(patternflyPackageJSONPath);

const config = {
    stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
    addons: [
        "@storybook/addon-controls",
        "@storybook/addon-links",
        "@storybook/addon-essentials",
        "storybook-addon-mock",
    ],
    staticDirs: [
        {
            from: join(patternflyPackagePath, "patternfly-base.css"),
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
    viteFinal({ plugins = [], ...config }) {
        const mergedConfig: InlineConfig = {
            ...config,
            define: {
                "process.env.NODE_ENV": JSON.stringify(NODE_ENV),
                "process.env.CWD": JSON.stringify(cwd()),
                "process.env.AK_API_BASE_PATH": JSON.stringify(process.env.AK_API_BASE_PATH || ""),
            },
            plugins: [
                modify({
                    find: importInlineRegexp,
                    replace: (match: RegExpMatchArray) => {
                        return `${match}?inline`;
                    },
                }),
                ...plugins,
                postcssLit(),
                tsconfigPaths(),
            ],
        };

        return mergedConfig;
    },
} satisfies StorybookConfig;

export default config;
