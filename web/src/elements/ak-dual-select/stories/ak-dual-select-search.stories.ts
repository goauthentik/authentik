import "@goauthentik/elements/messages/MessageContainer";
import { debounce } from "@goauthentik/elements/utils/debounce";
import { Meta, StoryObj } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../components/ak-search-bar";
import { AkSearchbar } from "../components/ak-search-bar";

const metadata: Meta<AkSearchbar> = {
    title: "Elements / Dual Select / Search Bar",
    component: "ak-dual-select-search",
    parameters: {
        docs: {
            description: {
                component: "A search input bar",
            },
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
        <div id="action-button-message-pad" style="margin-top: 1em"></div>
        <div id="action-button-message-pad-2" style="margin-top: 1em"></div>
    </div>`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayMessage = (result: any) => {
    const doc = new DOMParser().parseFromString(`<p><i>Content</i>: ${result}</p>`, "text/xml");
    const target = document.querySelector("#action-button-message-pad");
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    target!.replaceChildren(doc.firstChild!);
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayMessage2 = (result: any) => {
    console.debug("Huh.");
    const doc = new DOMParser().parseFromString(`<p><i>Behavior</i>: ${result}</p>`, "text/xml");
    const target = document.querySelector("#action-button-message-pad-2");
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    target!.replaceChildren(doc.firstChild!);
};

const displayMessage2b = debounce(displayMessage2, 250);

window.addEventListener("input", (event: Event) => {
    const message = (event.target as HTMLInputElement | undefined)?.value ?? "-- undefined --";
    displayMessage(message);
    displayMessage2b(message);
});

type Story = StoryObj;

export const Default: Story = {
    render: () => container(html` <ak-search-bar></ak-search-bar>`),
};
