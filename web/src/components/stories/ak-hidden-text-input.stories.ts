import "../ak-hidden-text-input.js";

import { type AkHiddenTextInput, type AkHiddenTextInputProps } from "../ak-hidden-text-input.js";

import { ifPresent } from "#elements/utils/attributes";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const metadata: Meta<AkHiddenTextInputProps> = {
    title: "Components / <ak-hidden-text-input>",
    component: "ak-hidden-text-input",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Hidden Text Input Component

A text-input field with a visibility control, so you can show/hide sensitive fields.
`,
            },
        },
        layout: "padded",
    },
    argTypes: {
        label: {
            control: "text",
            description: "Label text for the input field",
        },
        value: {
            control: "text",
            description: "Current value of the input",
        },
        revealed: {
            control: "boolean",
            description: "Whether the text is currently visible",
        },
        placeholder: {
            control: "text",
            description: "Placeholder text for the input",
        },
        required: {
            control: "boolean",
            description: "Whether the input is required",
        },
        inputHint: {
            control: "select",
            options: ["text", "code"],
            description: "Input type hint for styling and behavior",
        },
        showMessage: {
            control: "text",
            description: "Custom message for show action",
        },
        hideMessage: {
            control: "text",
            description: "Custom message for hide action",
        },
    },
};

export default metadata;

type Story = StoryObj<AkHiddenTextInput>;

const Template: Story = {
    args: {
        label: "Hidden Text Input",
        value: "",
        revealed: false,
    },
    render: (args) => html`
        <ak-hidden-text-input
            label=${ifPresent(args.label)}
            value=${ifPresent(args.value)}
            ?revealed=${args.revealed}
            placeholder=${ifPresent(args.placeholder)}
            ?required=${args.required}
            input-hint=${ifPresent(args.inputHint)}
            show-message=${ifPresent(args.showMessage)}
            hide-message=${ifPresent(args.hideMessage)}
        ></ak-hidden-text-input>
    `,
};

export const Password: Story = {
    ...Template,
    args: {
        label: "Password",
        placeholder: "Enter your password",
        required: true,
    },
};
