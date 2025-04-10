import { NodeEnvironment, resolvePackage, serializeEnvironmentVars } from "@goauthentik/monorepo";
import { PackageRoot } from "@goauthentik/web/paths";
import type { StorybookConfig } from "@storybook/web-components-vite";
import { deepmerge } from "deepmerge-ts";
import * as path from "node:path";
import modify from "rollup-plugin-modify";
import postcssLit from "rollup-plugin-postcss-lit";
import tsconfigPaths from "vite-tsconfig-paths";

const AK_API_BASE_PATH = process.env.AK_API_BASE_PATH || "";

const inlineImportPatterns = [
    'import AKGlobal from "(\\.\\./)*common/styles/authentik\\.css',
    'import AKGlobal from "@goauthentik/common/styles/authentik\\.css',
    'import PF.+ from "@patternfly/patternfly/\\S+\\.css',
    'import ThemeDark from "@goauthentik/common/styles/theme-dark\\.css',
    'import OneDark from "@goauthentik/common/styles/one-dark\\.css',
    'import styles from "\\./LibraryPageImpl\\.css',
];

const inlineImportPattern = new RegExp(inlineImportPatterns.map((a) => `(${a})`).join("|"));

const patternflyPath = resolvePackage("@patternfly/patternfly");

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
            from: path.resolve(patternflyPath, "patternfly-base.css"),
            to: "@patternfly/patternfly/patternfly-base.css",
        },
        {
            from: path.resolve(PackageRoot, "src", "common", "styles", "authentik.css"),
            to: "@goauthentik/common/styles/authentik.css",
        },
        {
            from: path.resolve(PackageRoot, "src", "common", "styles", "theme-dark.css"),
            to: "@goauthentik/common/styles/theme-dark.css",
        },
        {
            from: path.resolve(PackageRoot, "src", "common", "styles", "one-dark.css"),
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
        return deepmerge(config, {
            define: serializeEnvironmentVars({
                NODE_ENV: NodeEnvironment,
                CWD: process.cwd(),
                AK_API_BASE_PATH: AK_API_BASE_PATH,
                WATCHER_URL: "",
            }),

            plugins: [
                modify({
                    find: inlineImportPattern,
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
