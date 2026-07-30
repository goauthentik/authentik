/**
 * @file Storybook stories for the default Divider component implementation
 */

import "../Divider";

import { akDivider, type DividerProps } from "../Divider";

import { Meta, StoryObj } from "@storybook/web-components";

import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const meta: Meta<DividerProps> = {
    title: "Elements/Divider",
    component: "ak-divider",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `
A divider is a visual element that creates a thematic break or separation between content.
It can include optional content placed in the middle of the dividing line.
        `,
            },
        },
    },
    argTypes: {
        variant: {
            options: ["default", "strong", "subtle"],
            control: { type: "select" },
            description: "Visual variant of the divider",
            table: {
                type: { summary: "string" },
                defaultValue: { summary: "default" },
            },
        },
        orientation: {
            options: ["horizontal", "vertical"],
            control: { type: "radio" },
            description: "Orientation of the divider",
            table: {
                type: { summary: "string" },
                defaultValue: { summary: "horizontal" },
            },
        },
        content: {
            control: "text",
            description: "Content to display in the middle of the divider",
            table: {
                type: { summary: "string" },
            },
        },
    },
    args: {
        variant: "default",
        orientation: "horizontal",
        content: "",
    },
};

export default meta;

type Story = StoryObj<DividerProps>;

const describe = (story: string) => ({ docs: { description: { story } } });

// Base Divider: Simple horizontal divider (equivalent to <hr>)
export const Basic: Story = {
    args: {},
    parameters: describe("Basic divider with no content, equivalent to an HTML `<hr>` element."),
    render: (args) => html`
        <div style="padding: 2rem;">
            <p>Content before the divider</p>
            <ak-divider
                variant=${ifDefined(args.variant)}
                orientation=${ifDefined(args.orientation)}
                >${args.content ? html`<span>${args.content}</span>` : nothing}</ak-divider
            >
            <p>Content after the divider</p>
        </div>
    `,
};

// Divider with text content
export const WithText: Story = {
    args: {
        content: html`<span>OR</span>`,
    },
    parameters: describe("Divider with simple text content in the middle."),
    render: (args) => html`
        <div style="padding: 2rem;">
            <p>Option One</p>
            <ak-divider
                variant=${ifDefined(args.variant)}
                orientation=${ifDefined(args.orientation)}
                >${args.content}</ak-divider
            >
            <p>Option Two</p>
        </div>
    `,
};

// Divider with HTML content
export const WithHTML: Story = {
    parameters: describe("Divider with HTML content in the middle, such as an icon and text."),
    render: (args) => html`
        <div style="padding: 2rem;">
            <p>Section One</p>
            <ak-divider
                variant=${ifDefined(args.variant)}
                orientation=${ifDefined(args.orientation)}
            >
                <span style="display: inline-flex; align-items: center;">
                    <span style="margin-right: 0.5rem;">●</span> Section Break
                </span>
            </ak-divider>
            <p>Section Two</p>
        </div>
    `,
};

// Variants showcase
export const Variants: Story = {
    parameters: describe("Divider with different visual variants: default, strong, and subtle."),
    render: () => html`
        <div style="padding: 2rem; display: flex; flex-direction: column; gap: 2rem;">
            <div>
                <p><strong>Default Variant</strong></p>
                <ak-divider variant="default">Default</ak-divider>
            </div>

            <div>
                <p><strong>Strong Variant</strong></p>
                <ak-divider variant="strong">Strong</ak-divider>
            </div>

            <div>
                <p><strong>Subtle Variant</strong></p>
                <ak-divider variant="subtle">Subtle</ak-divider>
            </div>
        </div>
    `,
};

// Vertical divider
export const Vertical: Story = {
    args: {
        orientation: "vertical",
    },
    parameters: describe(
        "Divider with vertical orientation, useful for separating inline content.",
    ),
    render: (args) => html`
        <div style="padding: 2rem; display: flex; align-items: center; height: 100px;">
            <span>Left Content</span>
            <ak-divider variant=${ifDefined(args.variant)} orientation="vertical"
                >${args.content}</ak-divider
            >
            <span>Right Content</span>
        </div>
    `,
};

export const VerticalWithContent: Story = {
    args: {
        orientation: "vertical",
    },
    parameters: describe(
        "Divider with vertical orientation, useful for separating inline content.",
    ),
    render: (args) => html`
        <div style="padding: 2rem; display: flex; align-items: center; height: 100px;">
            <span>That's supposed to</span>
            <ak-divider
                variant=${ifDefined(args.variant)}
                orientation="vertical"
                style="margin: 0 0.5rem"
                ><span style="color: black">𝄞</span></ak-divider
            >
            <span>be a clef symbol.</span>
        </div>
    `,
};

// Helper function usage
export const HelperFunction: Story = {
    parameters: describe(
        "Using the `akDivider` helper function to create dividers programmatically.",
    ),
    render: () => html`
        <div style="padding: 2rem; display: flex; flex-direction: column; gap: 2rem;">
            <div>
                <p>Simple text with helper:</p>
                ${akDivider({ content: '"Simple text"' })}
            </div>

            <div>
                <p>HTML stuff with helper:</p>
                ${akDivider({
                    content: html`<code>Some</code>&nbsp;<strong style="color: rebeccapurple"
                            >HTML</strong
                        >&nbsp;<em>stuff</em>`,
                    variant: "strong",
                })}
            </div>
        </div>
    `,
};

// Custom styling
export const CustomStyling: Story = {
    parameters: describe("Customizing the divider appearance using CSS custom properties."),
    render: () => html`
        <style>
            .custom-divider {
                --pf-v5-c-divider--color: #0066cc;
                --pf-v5-c-divider--margin: 2rem 0;
                --pf-v5-c-divider--content-spacing: 1rem;
                --pf-v5-c-divider--border-width: 2px;
            }

            .custom-divider::part(content) {
                background-color: #f0f0f0;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-weight: bold;
            }
        </style>

        <div style="padding: 2rem;">
            <p>Content above the custom divider</p>
            <ak-divider class="custom-divider">Custom Styled</ak-divider>
            <p>Content below the custom divider</p>
        </div>
    `,
};

// Icon in divider
export const WithIcon: Story = {
    parameters: describe("Divider with an icon in the middle."),
    render: () => html`
        <div style="padding: 2rem;">
            <p>First section of content</p>
            <ak-divider>
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="16" />
                    <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
            </ak-divider>
            <p>Second section of content</p>
        </div>
    `,
};
