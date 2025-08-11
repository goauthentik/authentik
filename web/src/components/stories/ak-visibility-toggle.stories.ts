import "../ak-visibility-toggle.js";

import { type VisibilityToggle, type VisibilityToggleProps } from "../ak-visibility-toggle.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const metadata: Meta<VisibilityToggleProps> = {
    title: "Elements/<ak-visibility-toggle>",
    component: "ak-visibility-toggle",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Visibility Toggle Component

A straightforward two-state iconic button for toggling the visibility of sensitive content such as passwords, private keys, or other secret information.
                
- Use for sensitive content that users might want to temporarily reveal
- There are default hide/show messages for screen readers, but they can be overridden
- Clients always handle the state
- The \`open\` state is false by default; we assume you want sensitive content hidden at start
`,
            },
        },
        layout: "padded",
    },
    argTypes: {
        open: {
            control: "boolean",
            description: "Whether the toggle is in the 'show' state (true) or 'hide' state (false)",
        },
        showMessage: {
            control: "text",
            description:
                'Message for screen readers when in hide state (default: "Show field content")',
        },
        hideMessage: {
            control: "text",
            description:
                'Message for screen readers when in show state (default: "Hide field content")',
        },
        disabled: {
            control: "boolean",
            description: "Whether the button should be disabled (for demo purposes)",
        },
    },
};

export default metadata;

type Story = StoryObj<VisibilityToggle>;

const Template: Story = {
    args: {
        open: false,
        showMessage: "Show field content",
        hideMessage: "Hide field content",
    },
    render: (args) => html`
        <ak-visibility-toggle
            ?open=${args.open}
            show-message=${ifDefined(args.showMessage)}
            hide-message=${ifDefined(args.hideMessage)}
            @click=${(e: Event) => {
                const target = e.target as VisibilityToggle;
                target.open = !target.open;
                // In a real application, you would also toggle the visibility
                // of the associated content here
            }}
        ></ak-visibility-toggle>
    `,
};

// Password field integration example
export const PasswordFieldExample: Story = {
    args: {
        showMessage: "Reveal password",
        hideMessage: "Conceal password",
    },
    render: () => {
        let isVisible = false;

        const toggleVisibility = (e: Event) => {
            isVisible = !isVisible;
            const toggle = e.target as VisibilityToggle;
            const passwordField = document.querySelector("#demo-password") as HTMLInputElement;

            toggle.open = isVisible;
            if (passwordField) {
                passwordField.type = isVisible ? "text" : "password";
            }
        };

        return html`
            <div style="display: flex; flex-direction: column; gap: 1rem; max-width: 300px;">
                <label for="demo-password" style="font-weight: bold;">Password:</label>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <input
                        id="demo-password"
                        type="password"
                        value="supersecretpassword123"
                        style="flex: 1; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;"
                        readonly
                    />
                    <ak-visibility-toggle
                        ?open=${isVisible}
                        show-message="Show password"
                        hide-message="Hide password"
                        @click=${toggleVisibility}
                    ></ak-visibility-toggle>
                </div>
                <p style="font-size: 0.875rem; color: #666;">
                    Click the eye icon to toggle password visibility
                </p>
            </div>
        `;
    },
};
