import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { type ILabel, Label, PFColor } from "../Label.js";
import "../Label.js";

type ILabelForTesting = ILabel & { message: string };

const metadata: Meta<Label> = {
    title: "Elements/<ak-label>",
    component: "ak-label",
    parameters: {
        docs: {
            description: "An alert",
        },
    },
    argTypes: {
        compact: { control: "boolean" },
        color: { control: "text" },
        icon: { control: "text" },
        // @ts-ignore
        message: { control: "text" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        compact: false,
        message: "Eat at Joe's.",
    },

    // @ts-ignore
    render: ({ compact, color, icon, message }: ILabelForTesting) => {
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
            <style>
                ak-label {
                    display: inline-block;
                    width: 48rem;
                    max-width: 48rem;
                }
            </style>
            <ak-label color=${ifDefined(color)} ?compact=${compact} icon=${ifDefined(icon)}>
                <p>${message}</p>
            </ak-label>
        </div>`;
    },
};

export const SuccessLabel = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{
            color: PFColor.Green,
            message: html`I'll show them! I'll show them <i>all</i>&nbsp;! Mwahahahahaha!`,
        },
    },
};

export const CompactWarningLabel = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{
            compact: true,
            color: "warning",
            icon: "fa-coffee",
            message: "It is time for coffee.",
        },
    },
};

export const DangerLabel = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{ color: "danger", message: "Grave danger? Is there another kind?" },
    },
};
