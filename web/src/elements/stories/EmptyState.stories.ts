import type { Meta, StoryObj } from "@storybook/web-components";

import { TemplateResult, html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import "../EmptyState.js";
import { type EmptyState, type IEmptyState, akEmptyState } from "../EmptyState.js";

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
                component: `
# Empty State Component

The EmptyState is an in-page element to indicate that something is either loading or unavailable.
When "loading" is true it displays a spinner, otherwise it displays a static icon. The default
icon is a question mark in a circle.

It has three named slots:

- **heading**: Main title (renders in an \`h1\`)
- **body**: Any text to describe the state
- **primary**: Action buttons or other interactive elements
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
        fullHeight: false,
    },
    render: (args) => html`
        <ak-empty-state
            icon=${ifDefined(args.icon)}
            ?loading=${args.loading}
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

export const LoadingWithMessage: Story = {
    ...Template,
    args: {
        loading: true,
        headingText: html`<span>I <em>know</em> it's here, somewhere...</span>`,
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

export const EmptyAndLoading: Story = {
    render: (args) => html` <ak-empty-and-loading> </ak-empty-and-loading>`,
};

export const ProgrammaticUsage: Story = {
    ...Template,
    args: {
        icon: "fa-cubes",
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
