import "../Button";

import { type ButtonProps } from "../Button";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

type Renderable = string | TemplateResult;

type StoryArgs = ButtonProps & { content: Renderable };

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories#default-export
const metadata: Meta<StoryArgs> = {
    title: "Elements / Button",
    // This component will be used to render the component in the Stories
    component: "ak-button",
    // Define component tagName - this is optional, but helpful for auto-generation
    // The tag name will be used to generate the component's displayName
    tags: ["autodocs"],
    // More on argTypes: https://storybook.js.org/docs/api/argtypes
    argTypes: {
        variant: {
            control: "select",
            options: ["primary", "secondary", "tertiary", "control", "plain", "link"],
            description: "Button styling variant",
        },
        severity: {
            control: "select",
            options: [undefined, "danger", "warning"],
            description: "Button severity level (danger = red, warning = yellow)",
        },
        size: {
            control: "select",
            options: [undefined, "sm", "lg"],
            description: "Button size",
        },
        disabled: {
            control: "boolean",
            description: "Disables the button",
        },
        block: {
            control: "boolean",
            description: "Makes the button full width",
        },
        inline: {
            control: "boolean",
            description: "Renders button inline with text (link variant only)",
        },
        active: {
            control: "boolean",
            description: "Sets button to active state",
        },
        expanded: {
            control: "boolean",
            description: "Sets control variant button to expanded state",
        },
        type: {
            control: "select",
            options: ["button", "submit", "reset"],
            description: "Button type (for form interactions)",
        },
        href: {
            control: "text",
            description: "URL for link buttons (renders as <a>)",
        },
        target: {
            control: "text",
            description: "Target attribute for link buttons",
        },
        label: {
            control: "text",
            description: "Accessible label for screen readers",
        },
    },
    args: {
        content: "Do you feel lucky... punk?",
    },
    // https://storybook.js.org/docs/parameters
    parameters: {
        // https://storybook.js.org/docs/writing-docs/docs-page
        docs: {
            description: {
                component: `
# Button 

A button component based on PatternFly 5 design system.
`,
            },
        },
        // How to position stories: https://storybook.js.org/docs/configure/story-layout
        layout: "centered",
    },
};

export default metadata;

type Story = StoryObj<StoryArgs>;

const template = {
    render: (args: StoryArgs) => html`
        <ak-button
            variant=${ifDefined(args.variant)}
            ?disabled=${!!args.disabled}
            ?block=${!!args.block}
            ?active=${!!args.active}
            size=${ifDefined(args.size || undefined)}
            severity=${ifDefined(args.severity || undefined)}
            type=${ifDefined(args.type || undefined)}
            href=${ifDefined(args.href || undefined)}
            target=${ifDefined(args.target || undefined)}
            label=${ifDefined(args.label || undefined)}
        >
            ${args.content ?? "Button"}
        </ak-button>
    `,
};

// More on component templates: https://storybook.js.org/docs/writing-stories/introduction#using-args
export const Primary: Story = {
    ...template,
    args: {
        variant: "primary",
        content: "Primary",
    },
};

export const Secondary: Story = {
    ...template,
    args: {
        variant: "secondary",
        content: "Secondary",
    },
};

export const Tertiary: Story = {
    ...template,
    args: {
        variant: "tertiary",
        content: "Tertiary",
    },
};

export const Danger: Story = {
    ...template,
    args: {
        variant: "primary",
        severity: "danger",
        content: "Danger!",
    },
};

export const Warning: Story = {
    ...template,
    args: {
        variant: "primary",
        severity: "warning",
        content: "Warning",
    },
};

export const Small: Story = {
    ...template,
    args: {
        size: "sm",
        content: "Small Button",
    },
};

export const Large: Story = {
    ...template,
    args: {
        size: "lg",
        content: "Large Button",
    },
};

export const Disabled: Story = {
    ...template,
    args: {
        disabled: true,
        content: "Disabled Button",
    },
};

export const Block: Story = {
    ...template,
    args: {
        block: true,
        content: "You paid for the whole block, use the whole block",
    },
};

export const Link: Story = {
    ...template,
    args: {
        variant: "link",
        href: "https://goauthentik.io",
        target: "_blank",
        content: "Zeldaaaaa!",
    },
};

export const DisabledLink: Story = {
    ...template,
    args: {
        variant: "link",
        href: "https://goauthentik.io",
        target: "_blank",
        disabled: true,
        content: "Gerudo!",
    },
};

export const InlineLink: Story = {
    args: {
        variant: "link",
        href: "https://goauthentik.io",
        target: "_blank",
        inline: true,
    },
    render: (args) => html`
        <div>
            This is a paragraph with an
            <ak-button
                variant=${ifDefined(args.variant)}
                target=${ifDefined(args.target)}
                ?inline=${args.inline}
                ?disabled=${args.disabled}
                href=${ifDefined(args.href || undefined)}
            >
                inline link button
            </ak-button>
            in the middle of the text.
        </div>
    `,
};

export const Plain: Story = {
    ...template,
    args: {
        variant: "plain",
        content: html`<svg
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
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="16"></line>
            <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>`,
    },
};

export const Control: Story = {
    ...template,
    args: {
        variant: "control",
        content: "Control Button",
    },
};

export const ControlExpanded: Story = {
    ...template,
    args: {
        variant: "control",
        expanded: true,
        content: "Expanded Control",
    },
};

export const Active: Story = {
    ...template,
    args: {
        active: true,
        content: "Activated",
    },
};

export const FormSubmit: Story = {
    args: {
        type: "submit",
    },
    render: (args) => html`
        <form
            @submit=${(e: Event) => {
                e.preventDefault();
                // eslint-disable-next-line no-alert
                alert("Form submitted!");
            }}
        >
            <ak-button
                variant=${args.variant || "primary"}
                type=${ifDefined(args.type)}
                ?disabled=${!!args.disabled}
            >
                Submit Form
            </ak-button>
        </form>
    `,
};

export const FormReset: Story = {
    args: {
        type: "reset",
        variant: "secondary",
    },
    render: (args) => html`
        <form
            @reset=${() => {
                // eslint-disable-next-line no-alert
                alert("Form reset!");
            }}
        >
            <ak-button
                variant=${ifDefined(args.variant)}
                type=${ifDefined(args.type)}
                ?disabled=${!!args.disabled}
            >
                Reset Form
            </ak-button>
        </form>
    `,
};

export const AllVariants: Story = {
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 1rem; align-items: flex-start;">
            <ak-button variant="primary">Primary</ak-button>
            <ak-button variant="secondary">Secondary</ak-button>
            <ak-button variant="tertiary">Tertiary</ak-button>
            <ak-button variant="link">Link</ak-button>
            <ak-button variant="plain">
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
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="16"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
            </ak-button>
            <ak-button variant="control">Control</ak-button>
        </div>
    `,
};

export const AllSeverities: Story = {
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 1rem; align-items: flex-start;">
            <div style="display: flex; gap: 1rem;">
                <ak-button variant="primary">Default</ak-button>
                <ak-button variant="primary" severity="danger">Danger</ak-button>
                <ak-button variant="primary" severity="warning">Warning</ak-button>
            </div>
            <div style="display: flex; gap: 1rem;">
                <ak-button variant="secondary">Default</ak-button>
                <ak-button variant="secondary" severity="danger">Danger</ak-button>
            </div>
            <div style="display: flex; gap: 1rem;">
                <ak-button variant="link">Default</ak-button>
                <ak-button variant="link" severity="danger">Danger</ak-button>
            </div>
        </div>
    `,
};

export const AllSizes: Story = {
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 1rem; align-items: flex-start;">
            <div style="display: flex; gap: 1rem; align-items: center;">
                <ak-button variant="primary" size="sm">Small</ak-button>
                <ak-button variant="primary">Default</ak-button>
                <ak-button variant="primary" size="lg">Large</ak-button>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <ak-button variant="secondary" size="sm">Small</ak-button>
                <ak-button variant="secondary">Default</ak-button>
                <ak-button variant="secondary" size="lg">Large</ak-button>
            </div>
        </div>
    `,
};

export const NarrowSizes: Story = {
    render: () => html`
        <p style="margin-bottom: 1rem">
            Narrow buttons have very small padding around the label, while the label text still
            responds to t-shirt sizes.
        </p>
        <div style="display: flex; flex-direction: column; gap: 1rem; align-items: flex-start;">
            <div style="display: flex; gap: 1rem; align-items: center;">
                <ak-button narrow variant="primary" size="sm">Small</ak-button>
                <ak-button narrow variant="primary">Default</ak-button>
                <ak-button narrow variant="primary" size="lg">Large</ak-button>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <ak-button narrow variant="secondary" size="sm">Small</ak-button>
                <ak-button narrow variant="secondary">Default</ak-button>
                <ak-button narrow variant="secondary" size="lg">Large</ak-button>
            </div>
        </div>
    `,
};

export const States: Story = {
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 1rem; align-items: flex-start;">
            <div style="display: flex; gap: 1rem;">
                <ak-button variant="primary">Normal</ak-button>
                <ak-button variant="primary" active>Active</ak-button>
                <ak-button variant="primary" disabled>Disabled</ak-button>
            </div>
            <div style="display: flex; gap: 1rem;">
                <ak-button variant="secondary">Normal</ak-button>
                <ak-button variant="secondary" active>Active</ak-button>
                <ak-button variant="secondary" disabled>Disabled</ak-button>
            </div>
            <div style="display: flex; gap: 1rem;">
                <ak-button variant="control">Normal</ak-button>
                <ak-button variant="control" active>Active</ak-button>
                <ak-button variant="control" expanded>Expanded</ak-button>
                <ak-button variant="control" disabled>Disabled</ak-button>
            </div>
        </div>
    `,
};
