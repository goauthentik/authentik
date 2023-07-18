import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "./ak-token-copy-button";
import AKTokenCopyButton from "./ak-token-copy-button";

// For this test, we want each key to be unique so that the tester can
// be assured that the returned result is in fact going into the
// clipboard.

function makeid(length: number) {
    const sample = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    return new Array(length)
        .fill(" ")
        .map(() => sample.charAt(Math.floor(Math.random() * sample.length)))
        .join("");
}

// We want the display to be rich and comprehensive.  The next two functions provide
// a styled wrapper for the return messages, and a styled wrapper for each message.

const container = (testItem: TemplateResult) => html` <div style="background: #fff; padding: 2em">
    <style>
        li {
            display: block;
        }
        p {
            display: block;
            margin-top: 1em;
        }
        p + p {
            margin-top: 0.2em;
            padding-left: 2.5rem;
        }
    </style>
    <ak-message-container></ak-message-container>
    ${testItem}
    <p>Messages received from the button:</p>
    <ul id="action-button-message-pad" style="margin-top: 1em"></ul>
</div>`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayMessage = (result: any) => {
    console.log(result);
    const doc = new DOMParser().parseFromString(
        `<li><p><i>Event</i>: ${
            "result" in result.detail ? result.detail.result.key : result.detail.error
        }</p><p style="padding-left: 2.5rem">The key should also be in your clipboard</p></li>`,
        "text/xml",
    );
    const target = document.querySelector("#action-button-message-pad");
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    target!.appendChild(doc.firstChild!);
};

// The Four-State buttons each produce these events.  Capture them.

window.addEventListener("ak-button-success", displayMessage);
window.addEventListener("ak-button-failure", displayMessage);

const metadata: Meta<AKTokenCopyButton> = {
    title: "Elements / Token Copy Button",
    component: "ak-token-copy-button",
    parameters: {
        docs: {
            description: {
                component:
                    "A four-state button for asynchronous operations specialized to retrieve SSO tokens",
            },
        },
        mockData: [
            {
                url: "api/v3/core/tokens/foobar/view_key/",
                method: "GET",
                status: 200,
                response: () => {
                    return {
                        key: `ThisIsTheMockKeyYouShouldExpectToSeeOnSuccess-${makeid(5)}`,
                    };
                },
            },
        ],
    },
};

export default metadata;

export const ButtonWithSuccess = () => {
    return container(
        html`<ak-token-copy-button class="pf-m-primary" identifier="foobar"
            >3 Seconds to Foo</ak-token-copy-button
        >`,
    );
};
