/**
 * @file Storybook configuration.
 * @import {StorybookConfig} from "@storybook/web-components-vite";
 * @satisfies {StorybookConfig}
 */
const config = {
    stories: ["../dist/**/*.mdx", "../dist/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
    addons: ["@storybook/addon-links", "@storybook/addon-a11y", "@storybook/addon-docs"],
    framework: "@storybook/web-components-vite",
};
export default config;
