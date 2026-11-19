import "../ak-spinner";
import { akSpinner, type SpinnerProps } from "../ak-spinner";

import type { Meta, StoryObj } from "@storybook/web-components-vite";

import { html } from "lit";

const meta = {
    title: "Elements / <ak-spinner>",
    component: "ak-spinner",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `The P4 spinner.  Unless the consumer supplies them, the host gets \`role="progressbar"\` and \`aria-valuetext="Loading..."\`.`,
            },
        },
    },
    argTypes: {
        size: {
            control: { type: "select" },
            options: ["sm", "md", "lg", "xl"],
            description: "Diameter, from the `--pf-c-spinner--m-*--diameter` tokens",
        },
        inline: {
            control: "boolean",
            description: "Size to the surrounding text (1em); overrides `size`",
        },
    },
    args: {
        size: "md",
        inline: false,
    },
    render: (args: SpinnerProps) => akSpinner(args),
} satisfies Meta<SpinnerProps>;

export default meta;

type Story = StoryObj<SpinnerProps>;

export const Default: Story = {};

export const Sizes: Story = {
    render: () =>
        html`<div style="display: flex; gap: 2rem; align-items: center">
            ${(["sm", "md", "lg", "xl"] as const).map(
                (size) =>
                    html`<figure
                        style="margin: 0; display: grid; justify-items: center; gap: 0.5rem"
                    >
                        ${akSpinner({ size })}
                        <figcaption><code>${size}</code></figcaption>
                    </figure>`,
            )}
        </div>`,
};

export const InlineWithText: Story = {
    render: () =>
        html`<p style="font-size: 1rem">
                ${akSpinner({ inline: true })} Synchronizing users from LDAP...
            </p>
            <h2 style="font-size: 2rem">${akSpinner({ inline: true })} Loading applications</h2>`,
};

export const CustomColor: Story = {
    parameters: {
        docs: {
            description: {
                story: "Override `--pf-c-spinner--Color` on the spinner or any ancestor.",
            },
        },
    },
    render: () =>
        html`<div style="display: flex; gap: 2rem">
            <ak-spinner
                size="lg"
                style="--pf-c-spinner--Color: var(--pf-global--success-color--100)"
            ></ak-spinner>
            <ak-spinner
                size="lg"
                style="--pf-c-spinner--Color: var(--pf-global--danger-color--100)"
            ></ak-spinner>
        </div>`,
};

export const CustomAccessibleText: Story = {
    parameters: {
        docs: {
            description: {
                story: "A consumer-supplied `role` or `aria-valuetext` is left alone.",
            },
        },
    },
    render: () => akSpinner({ "size": "lg", "aria-valuetext": "Revoking sessions" }),
};
