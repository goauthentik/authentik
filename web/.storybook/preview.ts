import type { Preview } from "@storybook/web-components";

import "@goauthentik/common/styles/authentik.css";
import "@goauthentik/common/styles/theme-dark.css";
import "@patternfly/patternfly/components/Brand/brand.css";
import "@patternfly/patternfly/components/Page/page.css";
// .storybook/preview.js
import "@patternfly/patternfly/patternfly-base.css";

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
