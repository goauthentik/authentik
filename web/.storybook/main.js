/**
 * @file Storybook configuration.
 * @import { StorybookConfig } from "@storybook/web-components-vite";
 */

/**
 * @param {TemplateStringsArray} strings
 * @param  {...any} values
 * @returns {string}
 */
const html = (strings, ...values) => String.raw({ raw: strings }, ...values);

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
        // ---
        "@storybook/addon-links",
        "@storybook/addon-docs",
    ],
    framework: "@storybook/web-components-vite",
    viteFinal: async (config) => {
        return {
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
    },

    previewBody: (body) => html`
        <ak-skip-to-content></ak-skip-to-content>
        <ak-message-container></ak-message-container>

        ${body}
    `,
};

export default config;
