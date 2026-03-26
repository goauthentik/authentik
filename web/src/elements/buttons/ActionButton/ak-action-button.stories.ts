import "#elements/messages/MessageContainer";
import "./ak-action-button.js";

import AKActionButton from "./ak-action-button.js";

import { Meta } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<AKActionButton> = {
    title: "Elements / <ak-action-button>",
    component: "ak-action-button",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
An \`<ak-action-button>\` takes a zero-arity function (a function that takes no argument) that returns
a promise. Pressing the button runs the function and the results of the promise drive the behavior
of the button.

## Usage

\`\`\`Typescript
import "#elements/buttons/ActionButton/ak-action-button";
\`\`\`

\`\`\`html
<ak-action-button .apiRequest=\${somePromise}">Your message here</ak-action-button>
\`\`\`

`,
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
    html` <div style="padding: 2em">
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
        `<li><i>Event</i>: ${"result" in result.detail ? result.detail.result : result.detail.error}</li>`,
        "text/xml",
    );
    const target = document.querySelector("#action-button-message-pad");
    target!.appendChild(doc.firstChild!);
};

window.addEventListener("ak-button-success", displayMessage);
window.addEventListener("ak-button-failure", displayMessage);

export const ButtonWithSuccess = () => {
    const run = () =>
        new Promise<string>((resolve) =>
            setTimeout(() => {
                resolve("Success!");
            }, 3000),
        );

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
