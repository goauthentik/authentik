import "@goauthentik/admin/admin-settings/AdminSettingsFooterLinks.js";
import { FooterLinkInput } from "@goauthentik/admin/admin-settings/AdminSettingsFooterLinks.js";
import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj, WebComponentsRenderer } from "@storybook/web-components";
import { DecoratorFunction } from "storybook/internal/types";

import { html } from "lit";

import { FooterLink } from "@goauthentik/api";

import "../ak-array-input.js";
import { IArrayInput } from "../ak-array-input.js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Decorator = DecoratorFunction<WebComponentsRenderer, any>;

const metadata: Meta<IArrayInput<unknown>> = {
    title: "Elements / Array Input",
    component: "ak-array-input",
    parameters: {
        docs: {
            description: {
                component:
                    "A table input object, in which multiple rows of related inputs can be grouped.",
            },
        },
    },
    decorators: [
        (story: Decorator) => {
            window.setTimeout(() => {
                const menu = document.getElementById("ak-array-input");
                if (!menu) {
                    throw new Error("Test was not initialized correctly.");
                }
                const messages = document.getElementById("reported-value");
                menu.addEventListener("change", (event: Event) => {
                    if (!event?.target) {
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
                    <p>Story:</p>
                    ${
                        // @ts-expect-error The types for web components are not well-defined in Storybook yet }
                        story()
                    }
                    <div style="margin-top: 2rem">
                        <p>Reported value:</p>
                        <pre id="reported-value"></pre>
                    </div>
                </div>
            </div>`;
        },
    ],
};

export default metadata;

type Story = StoryObj;

const items: FooterLink[] = [
    { name: "authentik", href: "https://goauthentik.io" },
    { name: "authentik docs", href: "https://docs.goauthentik.io/docs/" },
];

export const Default: Story = {
    render: () =>
        html` <ak-array-input
            id="ak-array-input"
            .items=${items}
            .newItem=${() => ({ name: "", href: "" })}
            .row=${(f?: FooterLink) =>
                html`<ak-admin-settings-footer-link name="footerLink" .footerLink=${f}>
                </ak-admin-settings-footer-link>`}
            validate
        ></ak-array-input>`,
};
