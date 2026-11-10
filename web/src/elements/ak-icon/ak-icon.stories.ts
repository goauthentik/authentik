import "./ak-icon.js";
import { akIcon, type IconProps } from "./ak-icon.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

// Keep in step with ak-icon.root.css.
const TOKENS = [
    "status.success",
    "status.warning",
    "status.danger",
    "status.info",
    "status.help",
    "action.close",
    "action.show",
    "action.hide",
    "object.user",
    "object.key",
] as const;

const meta: Meta<IconProps> = {
    title: "Elements/Icon",
    component: "ak-icon",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `
A single-color icon drawn from the CSS icon catalog in \`ak-icon.root.css\`. The icon takes its
color and size from the surrounding text. Each token is a CSS Custom Property, so a brand can
replace any icon with one line of custom CSS.
`,
            },
        },
    },
    argTypes: {
        name: {
            options: [...TOKENS, "does.not-exist"],
            control: { type: "select" },
            description: "Icon token",
            table: { type: { summary: "string" } },
        },
        label: {
            control: "text",
            description: "Accessible name; leave empty for a decorative icon",
            table: { type: { summary: "string" } },
        },
    },
    args: {
        name: "status.success",
        label: "",
    },
};

export default meta;

type Story = StoryObj<IconProps>;

export const Default: Story = {
    render: ({ name, label }) =>
        html`<span style="font-size: 2rem">${akIcon({ name, label: label || undefined })}</span>`,
};

export const Catalog: Story = {
    render: () => html`
        <ul
            style="display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: 1rem; list-style: none; padding: 0; font-size: 1rem;"
        >
            ${TOKENS.map(
                (name) => html`
                    <li style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon name=${name} style="font-size: 1.5rem"></ak-icon
                        ><code>${name}</code>
                    </li>
                `,
            )}
        </ul>
    `,
};

export const InheritsColorAndSize: Story = {
    render: () => html`
        <p style="color: var(--pf-global--success-color--100, green);">
            <ak-icon name="status.success"></ak-icon> Saved
        </p>
        <p style="color: var(--pf-global--danger-color--100, firebrick); font-size: 1.5rem;">
            <ak-icon name="status.danger"></ak-icon> Could not save
        </p>
        <h1 style="font-size: 3rem;"><ak-icon name="object.user"></ak-icon> akadmin</h1>
    `,
};

export const BrandOverride: Story = {
    parameters: {
        docs: {
            description: {
                story: `A brand redefines the token in its custom CSS. Here it is scoped to one
element; in practice it would be \`:root\`.`,
            },
        },
    },
    render: () => html`
        <style>
            .brand-demo {
                --ak-icon-status-success: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill-rule='evenodd' d='M3 3h18v18H3ZM10.6 16.2 6.3 11.9 7.7 10.5 10.6 13.4 16.9 7.1 18.3 8.5Z'/%3E%3C/svg%3E");
            }
        </style>
        <p style="font-size: 2rem;">
            <span>Default <ak-icon name="status.success"></ak-icon></span>
            <span class="brand-demo">Brand <ak-icon name="status.success"></ak-icon></span>
        </p>
    `,
};

export const UnknownToken: Story = {
    render: () => html`<p style="font-size: 2rem;"><ak-icon name="does.not-exist"></ak-icon></p>`,
};
