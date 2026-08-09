import "../EmptyState.js";

import { akEmptyState, type IEmptyState } from "../EmptyState.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, nothing, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

type StoryArgs = IEmptyState & {
    headingText?: string | TemplateResult;
    bodyText?: string | TemplateResult;
    primaryButtonText?: string | TemplateResult;
};

const metadata: Meta<StoryArgs> = {
    title: "Elements / <ak-empty-state>",
    component: "ak-empty-state",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Empty State Component

The EmptyState is an in-page element to indicate that something is either loading or unavailable.
When "loading" is true it displays a spinner, otherwise it displays a static icon. The default
icon is a question mark in a circle.

It has three named slots:

- The default slot: The heading (renders larger and more bold)
- **body**: Any text to describe the state
- **primary**: Action buttons or other interactive elements

For the loading attributes:

- The attribute \`loading\` will show the spinner
- The attribute \`default\` will show the spinner and the default header of "Loading"

If either of these attributes is active and the element contains content not assigned to one of the
named slots, it will be shown in the header.  This overrides the default text of \`default\`.  You
do not need both attributes for \`default\` to work; it assumes loading.

`,
            },
        },
        layout: "padded",
    },
    argTypes: {
        icon: {
            control: "text",
            description: "Font Awesome icon class (without 'fa-' prefix)",
        },
        loading: {
            control: "boolean",
            description: "Show loading spinner instead of icon",
        },
        defaultLabel: {
            control: "boolean",
            description: "Show loading spinner instead of icon",
        },
        fullHeight: {
            control: "boolean",
            description: "Fill the full height of container",
        },
        headingText: {
            control: "text",
            description: "Text for heading slot (for demo purposes)",
        },
        bodyText: {
            control: "text",
            description: "Text for body slot (for demo purposes)",
        },
        primaryButtonText: {
            control: "text",
            description: "Text for primary button (for demo purposes)",
        },
    },
};

export default metadata;

type Story = StoryObj<StoryArgs>;

const Template: Story = {
    args: {
        icon: "fa-circle-radiation",
        loading: false,
        defaultLabel: false,
        fullHeight: false,
    },
    render: (args) => html`
        <ak-empty-state
            icon=${ifDefined(args.icon)}
            ?loading=${args.loading}
            ?default-label=${args.defaultLabel}
            ?full-height=${args.fullHeight}
        >
            ${args.headingText ? html`<span>${args.headingText}</span>` : nothing}
            ${args.bodyText ? html`<span slot="body">${args.bodyText}</span>` : nothing}
            ${args.primaryButtonText
                ? html`
                      <button slot="primary" class="pf-c-button pf-m-primary">
                          ${args.primaryButtonText}
                      </button>
                  `
                : nothing}
        </ak-empty-state>
    `,
};

export const Basic: Story = {
    ...Template,
    args: {
        icon: "fa-folder-open",
        headingText: "No files found",
        bodyText: "This folder is empty. Upload some files to get started.",
    },
};

export const Empty: Story = {
    ...Template,
    args: {
        icon: "",
    },
    render: () =>
        html`<p>Note that a completely empty &lt;ak-empty-state&gt; is just that: empty.</p>
            <ak-empty-state></ak-empty-state>`,
};

export const WithAction: Story = {
    ...Template,
    args: {
        icon: "fa-users",
        headingText: "No users yet",
        bodyText: "Get started by creating your first user account.",
        primaryButtonText: html`<button>Create User</button>`,
    },
};

export const Loading: Story = {
    ...Template,
    args: {
        loading: true,
    },
};

export const LoadingWithCustomMessage: Story = {
    ...Template,
    args: {
        loading: true,
        headingText: html`<span>I <em>know</em> it's here, somewhere...</span>`,
    },
};

export const LoadingWithDefaultMessage: Story = {
    ...Template,
    args: {
        defaultLabel: true,
    },
};

export const LoadingDefaultWithOverride: Story = {
    ...Template,
    args: {
        defaultLabel: true,
        headingText: html`<span>Have they got a chance? Eh. It would take a miracle.</span>`,
    },
};

export const LoadingDefaultWithButton: Story = {
    ...Template,
    args: {
        defaultLabel: true,
        primaryButtonText: html`<button>Cancel</button>`,
    },
};

export const FullHeight: Story = {
    ...Template,
    args: {
        icon: "fa-search",
        headingText: "No search results",
        bodyText: "Try adjusting your search criteria or browse our categories.",
        fullHeight: true,
        primaryButtonText: html`<button>Go back</button>`,
    },
};

export const ProgrammaticUsage: Story = {
    ...Template,
    args: {
        icon: "fa-beer",
        headingText: "Hold My Beer",
        bodyText: "I saw this in a cartoon once. I'm sure I can pull it off.",
        primaryButtonText: html`<button>Leave The Scene Immediately</button>`,
    },
    render: (args) =>
        akEmptyState(
            {
                icon: args.icon,
            },
            {
                heading: args.headingText,
                body: args.bodyText,
                primary: args.primaryButtonText
                    ? html`
                          <button slot="primary" class="pf-c-button pf-m-primary">
                              ${args.primaryButtonText}
                          </button>
                      `
                    : undefined,
            },
        ),
};

export const IconShowcase: Story = {
    args: {},
    render: () => html`
        <div
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;"
        >
            <ak-empty-state icon="fa-users">
                <span>Users</span>
                <span slot="body">No users found</span>
            </ak-empty-state>

            <ak-empty-state icon="fa-database">
                <span>Database</span>
                <span slot="body">No records</span>
            </ak-empty-state>

            <ak-empty-state icon="fa-envelope">
                <span>Messages</span>
                <span slot="body">No messages</span>
            </ak-empty-state>

            <ak-empty-state icon="fa-chart-bar">
                <span>Analytics</span>
                <span slot="body">No data to display</span>
            </ak-empty-state>

            <ak-empty-state icon="fa-cog">
                <span>Settings</span>
                <span slot="body">No configuration</span>
            </ak-empty-state>

            <ak-empty-state icon="fa-shield-alt">
                <span>Security</span>
                <span slot="body">No alerts</span>
            </ak-empty-state>
        </div>
    `,
};
