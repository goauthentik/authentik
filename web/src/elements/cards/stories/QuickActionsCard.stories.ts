import "../QuickActionsCard.js";

import { QuickAction, QuickActionsCard } from "../QuickActionsCard.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const ACTIONS: QuickAction[] = [
    ["Create a new application", "/core/applications"],
    ["Check the logs", "/events/log"],
    ["Explore integrations", "https://integrations.goauthentik.io/", true],
    ["Manage users", "/identity/users"],
    ["Check the release notes", "https://docs.goauthentik.io/releases/", true],
];

const metadata: Meta<QuickActionsCard> = {
    title: "Elements/<ak-quick-action-card>",
    component: "ak-quick-action-card",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Quick Action Cards

A Quick Action Card displays a list of navigation links. It is used on our dashboards to provide
easy access to basic operations implied by the dashboard. The example here is from the home page
dashboard.

The QuickAction type has three fields: the string to display, the URL to navigate to, and a flag
indicating if the browser should open the link in a new tab.

## Usage

\`\`\`Typescript
import "@goauthentik/web/elements/cards/QuickActionsCard";

const ACTIONS: QuickAction[] = [
    ["Create a new application", "/core/applications"],
    ["Check the logs", "/events/log"],
    ["Explore integrations", "https://goauthentik.io/integrations/", true],
    ["Manage users", "/identity/users"],
    ["Check the release notes", "https://docs.goauthentik.io/releases/", true],
];
\`\`\`

\`\`\`html
<ak-quick-actions-card title="Some title" .actions=\${ACTIONS}></ak-aggregate-card>
\`\`\`
`,
            },
        },
    },
    argTypes: {
        title: { control: "text" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        title: "Quick actions",
    },
    render: ({ title }) => {
        return html`
            <style>
                ak-quick-actions-card {
                    display: inline-block;
                    width: 16rem;
                    max-width: 16rem;
                }
            </style>
            <ak-quick-actions-card title=${title} .actions=${ACTIONS}></ak-quick-actions-card>
        `;
    },
};
