import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj, WebComponentsRenderer } from "@storybook/web-components";
import { DecoratorFunction } from "storybook/internal/types";

import { html } from "lit";

import { FooterLinkInput } from "../AdminSettingsFooterLinks.js";
import "../AdminSettingsFooterLinks.js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Decorator = DecoratorFunction<WebComponentsRenderer, any>;

const metadata: Meta<FooterLinkInput> = {
    title: "Components / Footer Link Input",
    component: "ak-admin-settings-footer-link",
    parameters: {
        docs: {
            description: {
                component: "A stylized control for the footer links",
            },
        },
    },
    decorators: [
        (story: Decorator) => {
            window.setTimeout(() => {
                const control = document.getElementById("footer-link");
                if (!control) {
                    throw new Error("Test was not initialized correctly.");
                }
                const messages = document.getElementById("reported-value");
                control.addEventListener("change", (event: Event) => {
                    if (!event.target) {
                        return;
                    }
                    const target = event.target as FooterLinkInput;
                    messages!.innerText = `${JSON.stringify(target.json(), null, 2)}\n\nValid: ${target.isValid ? "Yes" : "No"}`;
                });
            }, 250);

            return html`<div
                style="background: #fff; padding: 2em; position: relative"
                id="the-main-event"
            >
                <style>
                    li {
                        display: block;
                    }
                    p {
                        margin-top: 1em;
                    }
                    #the-answer-block {
                        padding-top: 3em;
                    }
                </style>
                <div>
                    ${
                        // @ts-expect-error The types for web components are not well-defined }
                        story()
                    }
                </div>
                <div style="margin-top: 2rem">
                    <p>Reported value:</p>
                    <pre id="reported-value"></pre>
                </div>
            </div>`;
        },
    ],
};

export default metadata;

type Story = StoryObj;

export const Default: Story = {
    render: () =>
        html` <ak-admin-settings-footer-link
            id="footer-link"
            name="the-footer"
        ></ak-admin-settings-footer-link>`,
};
