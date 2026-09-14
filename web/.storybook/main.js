/**
 * @file Storybook configuration.
 * @import { StorybookConfig } from "@storybook/web-components-vite";
 */

import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { copyAssets } from "../scripts/build-assets.mjs";

/**
 * @param {TemplateStringsArray} strings
 * @param  {...any} values
 * @returns {string}
 */
const html = (strings, ...values) => String.raw({ raw: strings }, ...values);

await copyAssets();

const __dirname = fileURLToPath(new URL(".", import.meta.url));

/**
 * @satisfies {StorybookConfig}
 */
const config = {
    stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
    staticDirs: [{ from: "../dist/assets", to: "/static/dist/assets" }],
    addons: [
        // ---
        "@storybook/addon-links",
        "@storybook/addon-docs",
    ],
    framework: "@storybook/web-components-vite",
    viteFinal: async (config) => {
        const newConfig = {
            ...config,
            define: {
                ...config.define,
                "import.meta.env.AK_BUNDLER": JSON.stringify("storybook"),
            },
            resolve: {
                ...config.resolve,
                // Avoid multiple instances of web components packages.
                conditions: [],
            },
        };
        newConfig.server = config.server || {};
        newConfig.server.fs = newConfig.server.fs || {};
        newConfig.server.fs.allow = newConfig.server.fs.allow || [];
        newConfig.server.fs.allow.push(join(__dirname, "../../packages/fonts"));
        newConfig.server.fs.allow.push(join(__dirname, ".."));
        return newConfig;
    },

    previewBody: (body) => html`
        <ak-skip-to-content></ak-skip-to-content>
        <ak-message-container></ak-message-container>

        ${body}
    `,
};

export default config;
