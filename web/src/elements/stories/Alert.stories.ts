import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

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
        warning: { control: "boolean" },
        info: { control: "boolean" },
        success: { control: "boolean" },
        danger: { control: "boolean" },
        // @ts-ignore
        message: { control: "text" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        inline: false,
        warning: false,
        info: false,
        success: false,
        danger: false,
        message: "You should be alarmed.",
    },

    // @ts-ignore
    render: ({ inline, warning, info, success, danger, message }: IAlertForTesting) => {
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
            <style>
                ak-alert {
                    display: inline-block;
                    width: 32rem;
                    max-width: 32rem;
                }
            </style>
            <ak-alert
                ?inline=${inline}
                ?warning=${warning}
                ?info=${info}
                ?success=${success}
                ?danger=${danger}
            >
                <p>${message}</p>
            </ak-alert>
        </div>`;
    },
};

export const SuccessAlert = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ success: true, message: "He's a tribute to your genius!" } },
};

export const InfoAlert = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ info: true, message: "An octopus has tastebuds on its arms." } },
};

export const DangerAlert = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ danger: true, message: "Danger, Will Robinson!  Danger!" } },
};
