import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "./ak-action-button";
import AKActionButton from "./ak-action-button";

const metadata: Meta<AKActionButton> = {
    title: "Elements / Action Button",
    component: "ak-action-button",
    parameters: {
        docs: {
            description: {
                component: "A four-state button for asynchronous operations",
            },
        },
    },
    argTypes: {
        apiRequest: {
            type: "function",
            description:
                "Asynchronous function that takes no arguments and returns a Promise.  The contents of the completed Promise will be sent with the ak-button-success event.",
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #fff; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        <ak-message-container></ak-message-container>
        ${testItem}
        <p>Messages received from the button:</p>
        <ul id="action-button-message-pad" style="margin-top: 1em"></ul>
    </div>`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayMessage = (result: any) => {
    const doc = new DOMParser().parseFromString(
        `<li><i>Event</i>: ${
            "result" in result.detail ? result.detail.result : result.detail.error
        }</li>`,
        "text/xml",
    );
    const target = document.querySelector("#action-button-message-pad");
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    target!.appendChild(doc.firstChild!);
};

window.addEventListener("ak-button-success", displayMessage);
window.addEventListener("ak-button-failure", displayMessage);

export const ButtonWithSuccess = () => {
    const run = () =>
        new Promise<string>(function (resolve) {
            setTimeout(function () {
                resolve("Success!");
            }, 3000);
        });

    return container(
        html`<ak-action-button class="pf-m-primary" .apiRequest=${run}
            >3 Seconds</ak-action-button
        >`,
    );
};

export const ButtonWithError = () => {
    const run = () =>
        new Promise((resolve, reject) => {
            setTimeout(() => {
                reject(new Error("This is the error message."));
            }, 3000);
        });

    return container(
        html` <ak-action-button class="pf-m-secondary" .apiRequest=${run}
            >3 Seconds</ak-action-button
        >`,
    );
};
