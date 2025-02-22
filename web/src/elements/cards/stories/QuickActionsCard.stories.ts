import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "../QuickActionsCard.js";
import { QuickAction, QuickActionsCard } from "../QuickActionsCard.js";

const ACTIONS: QuickAction[] = [
    ["Create a new application", "/core/applications"],
    ["Check the logs", "/events/log"],
    ["Explore integrations", "https://goauthentik.io/integrations/", true],
    ["Manage users", "/identity/users"],
    ["Check the release notes", "https://goauthentik.io/docs/releases/", true],
];

const metadata: Meta<QuickActionsCard> = {
    title: "Elements/<ak-quick-action-card>",
    component: "ak-quick-action-card",
    parameters: {
        docs: {
            description: "A specialized card for a list of navigation links",
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
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
            <style>
                ak-quick-actions-card {
                    display: inline-block;
                    width: 16rem;
                    max-width: 16rem;
                }
            </style>
            <ak-quick-actions-card title=${title} .actions=${ACTIONS}></ak-quick-actions-card>
        </div>`;
    },
};
