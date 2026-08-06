/**
 * @file Storybook Preview 
 * @import {Preview} from "@storybook/web-components-vite";
 */

import "@goauthentik/fonts/faces.css";
import "@goauthentik/fonts/icons.css";
import "@goauthentik/theme/index.css";
import "@goauthentik/elements/styles/Divider.root.css";
import "@goauthentik/elements/styles/Progress.root.css";
import "@goauthentik/elements/styles/ToggleGroup.root.css";
import "./preview.css";

/*
 * @satisfies {Preview}
 */
const preview = {
    parameters: {
        controls: {
            matchers: {
                color: /(background|color)$/i,
                date: /Date$/i,
            },
        },

        a11y: {
            // 'todo' - show a11y violations in the test UI only
            // 'error' - fail CI on a11y violations
            // 'off' - skip a11y checks entirely
            test: "todo",
        },
    },
};

export default preview;
