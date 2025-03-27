import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { Alert, type IAlert } from "../Alert.js";
import "../Alert.js";

type IAlertForTesting = IAlert & { message: string };

const metadata: Meta<Alert> = {
    title: "Elements/<ak-alert>",
    component: "ak-alert",
    parameters: {
        docs: {
            description: "An alert",
        },
    },
    argTypes: {
        inline: { control: "boolean" },
        level: { control: "text" },
        icon: { control: "text" },
        // @ts-expect-error TODO: Clarify
        message: { control: "text" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        inline: false,
        message: "You should be alarmed.",
    },

    // @ts-expect-error TODO: Clarify
    render: ({ inline, level, icon, message }: IAlertForTesting) => {
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
            <style>
                ak-alert {
                    display: inline-block;
                    width: 32rem;
                    max-width: 32rem;
                }
            </style>
            <ak-alert level=${ifDefined(level)} ?inline=${inline} icon=${ifDefined(icon)}>
                <p>${message}</p>
            </ak-alert>
        </div>`;
    },
};

export const SuccessAlert = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ level: "success", message: "He's a tribute to your genius!" } },
};

export const InfoAlert = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{ level: "info", icon: "fa-coffee", message: "It is time for coffee." },
    },
};

export const DangerAlert = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ level: "danger", message: "Danger, Will Robinson!  Danger!" } },
};
