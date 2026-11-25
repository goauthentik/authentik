import { AKFormErrors, AKFormErrorsProps } from "#components/ak-field-errors";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const metadata: Meta<AKFormErrorsProps> = {
    title: "Components / Field Errors",
    parameters: {
        docs: {
            description: {
                component: `
# Field Errors

A function component that renders a list of form field errors.  Accepts almost anything.
Handles both flat and nested error lists.
`,
            },
        },
    },
    render: (args) => html`<div class="pf-c-form__group">${AKFormErrors(args)}</div>`,
};

export default metadata;

type Story = StoryObj<AKFormErrorsProps>;

export const SingleString: Story = {
    args: { errors: ["This field is required."] },
};

export const FieldTuples: Story = {
    args: {
        errors: [
            ["username", "A user with that username already exists."],
            ["email", "Enter a valid email address."],
        ],
    },
};

export const MixedSources: Story = {
    args: {
        errors: [
            "A plain string error.",
            new Error("An Error object's message."),
            { string: "An ErrorDetail from the API.", code: "invalid" },
            { detail: "An object with a detail key." },
        ],
    },
};

export const ValidationErrors: Story = {
    args: {
        errors: [
            {
                nonFieldErrors: ["Passwords do not match.", "Password is too short."],
                code: "invalid",
            },
        ],
    },
};

export const Empty: Story = {
    args: { errors: [] },
};
