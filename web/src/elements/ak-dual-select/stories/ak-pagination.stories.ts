import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../components/ak-pagination";
import { AkPagination } from "../components/ak-pagination";
import { DualSelectPaginatorNavEvent } from "../events";

const metadata: Meta<AkPagination> = {
    title: "Elements / Dual Select / Pagination Control",
    component: "ak-pagination",
    parameters: {
        docs: {
            description: {
                component: "The Pagination Control",
            },
        },
    },
    argTypes: {
        pages: {
            type: "string",
            description: "An authentik Pagination struct",
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
const handleMoveChanged = (result: DualSelectPaginatorNavEvent) => {
    console.debug(result);
    const target = document.querySelector("#action-button-message-pad");
    target!.append(
        new DOMParser().parseFromString(
            `<li>Request to move to page ${result.page}</li>`,
            "text/xml",
        ).firstChild!,
    );
};

window.addEventListener(DualSelectPaginatorNavEvent.eventName, handleMoveChanged);

type Story = StoryObj;

const pages = {
    count: 44,
    startIndex: 1,
    endIndex: 20,
    next: 2,
    previous: 0,
};

export const Default: Story = {
    render: () => container(html` <ak-pagination .pages=${pages}></ak-pagination>`),
};

const morePages = {
    count: 86,
    startIndex: 21,
    endIndex: 40,
    next: 3,
    previous: 1,
};

export const More: Story = {
    render: () => container(html` <ak-pagination .pages=${morePages}></ak-pagination>`),
};
