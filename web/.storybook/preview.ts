import type { Preview } from "@storybook/web-components";

// .storybook/preview.js

const preview: Preview = {
    parameters: {
        actions: { argTypesRegex: "^on[A-Z].*" },
        cssUserPrefs: {
            "prefers-color-scheme": "light",
        },
        controls: {
            matchers: {
                color: /(background|color)$/i,
                date: /Date$/,
            },
        },
    },
};

export default preview;
