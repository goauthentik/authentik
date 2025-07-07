import { EVENT_MESSAGE } from "@goauthentik/common/constants";
import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { TemplateResult, html } from "lit";

import "../ak-list-select.js";
import { ListSelect } from "../ak-list-select.js";
import { groupedSampleData, sampleData } from "./sampleData.js";

const longGoodForYouPairs = {
    grouped: false,
    options: sampleData.map(({ produce }) => [slug(produce), produce]),
};

const metadata: Meta<ListSelect> = {
    title: "Elements / List Select",
    component: "ak-list-select",
    parameters: {
        docs: {
            description: {
                component: "A scrolling component from which elements can be selected",
            },
        },
    },
    argTypes: {
        options: {
            type: "string",
            description: "An array of [key, label, desc] pairs of what to show",
        },
    },
};

export default metadata;

type Story = StoryObj;

const sendMessage = (message: string) =>
    document.dispatchEvent(
        new CustomEvent(EVENT_MESSAGE, { bubbles: true, composed: true, detail: { message } }),
    );

const container = (testItem: TemplateResult) => {
    window.setTimeout(() => {
        const menu = document.getElementById("ak-list-select");
        if (!menu) {
            throw new Error("Test was not initialized correctly.");
        }
        menu.addEventListener("focusin", () => sendMessage("Element received focus"));
        menu.addEventListener("blur", () => sendMessage("Element lost focus"));
        menu.addEventListener("change", (event: Event) =>
            sendMessage(`Value changed to: ${(event.target as HTMLInputElement)?.value}`),
        );
    }, 250);

    return html` <div
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
        <ak-message-container></ak-message-container>
        ${testItem}
    </div>`;
};

export const Default: Story = {
    render: () =>
        container(
            html` <ak-list-select
                id="ak-list-select"
                style="top: 1em; left: 1em"
                .options=${longGoodForYouPairs}
            ></ak-list-select>`,
        ),
};

export const Grouped: Story = {
    render: () =>
        container(
            html` <ak-list-select
                id="ak-list-select"
                style="top: 1em; left: 1em"
                .options=${groupedSampleData}
            ></ak-list-select>`,
        ),
};
