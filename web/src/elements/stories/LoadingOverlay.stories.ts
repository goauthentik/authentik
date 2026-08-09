import "../LoadingOverlay.js";

import { akLoadingOverlay, type ILoadingOverlay } from "../LoadingOverlay.js";

import { ifPresent } from "#elements/utils/attributes";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

type StoryArgs = ILoadingOverlay & {
    headingText?: string;
    bodyText?: string;
    noSpinner: boolean;
};

const metadata: Meta<StoryArgs> = {
    title: "Elements/ <ak-loading-overlay>",
    component: "ak-loading-overlay",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Loading Overlay Component

A full-screen overlay component that displays a loading state with optional heading and body content.

A variant of the EmptyState component that includes a protective background for load or import
operations during which the user should be prevented from interacting with the page.

It has two named slots, both optional:

- **heading**: Main title (renders in an \`<h1>\`)
- **body**: Any text to describe the state
`,
            },
        },
    },
    argTypes: {
        topmost: {
            control: "boolean",
            description:
                "Whether this overlay should appear above all other overlays (z-index: 999)",
            defaultValue: false,
        },
        noSpinner: {
            control: "boolean",
            description: "Disable the loading spinner animation",
            defaultValue: false,
        },
        icon: {
            control: "text",
            description: "Icon name to display instead of the default loading spinner",
        },
        headingText: {
            control: "text",
            description: "Heading text displayed above the loading indicator",
        },
        bodyText: {
            control: "text",
            description: "Body text displayed below the loading indicator",
        },
    },
    decorators: [
        (story) => html`
            <div
                style="position: relative; height: 400px; width: 100%; border: 1px solid #ccc; background: #f5f5f5;"
            >
                <div style="padding: 20px;">
                    <h3>Content Behind Overlay</h3>
                    <p>authentik is awesome (or will be if something were actually loading)</p>
                    <button>Sample Button</button>
                </div>
                ${story()}
            </div>
        `,
    ],
};

export default metadata;

type Story = StoryObj<StoryArgs>;

export const Default: Story = {
    render: () => html`<ak-loading-overlay></ak-loading-overlay>`,
};

export const WithHeading: Story = {
    args: {
        headingText: "Loading Data",
    },
    render: (args) =>
        html`<ak-loading-overlay>
            <span>${args.headingText}</span>
        </ak-loading-overlay>`,
};

export const WithHeadingAndBody: Story = {
    args: {
        headingText: "Loading Data",
        bodyText: "Please wait while we fetch your information...",
    },
    render: (args) =>
        html`<ak-loading-overlay>
            <span>${args.headingText}</span>
            <span slot="body">${args.bodyText}</span>
        </ak-loading-overlay>`,
};

export const NoSpinner: Story = {
    args: {
        headingText: "Static Message",
        bodyText: "This overlay shows without a spinner animation.",
    },
    render: (args) =>
        html`<ak-loading-overlay no-spinner>
            <span>${args.headingText}</span>
            <span slot="body">${args.bodyText}</span>
        </ak-loading-overlay>`,
};

export const WithCustomIcon: Story = {
    args: {
        icon: "fa-info-circle",
        headingText: "Processing",
        bodyText: "Your request is being processed...",
    },
    render: (args) =>
        html`<ak-loading-overlay no-spinner icon=${ifPresent(args.icon)}>
            <span>${args.headingText}</span>
            <span slot="body">${args.bodyText}</span>
        </ak-loading-overlay>`,
};

export const ProgrammaticUsage: Story = {
    args: {
        topmost: false,
        noSpinner: false,
        icon: "",
        headingText: "Programmatic Loading",
        bodyText: "This overlay was created using the akLoadingOverlay function.",
    },
    render: (args) =>
        akLoadingOverlay(
            {
                topmost: args.topmost,
                noSpinner: args.noSpinner,
                icon: args.icon || undefined,
            },
            {
                heading: args.headingText,
                body: args.bodyText,
            },
        ),
};
