import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { TemplateResult, html } from "lit";

import { SearchSelectSelectMenuEvent } from "../SearchSelectEvents.js";
import "../ak-search-select-menu.js";
import { SearchSelectMenu } from "../ak-search-select-menu.js";
import { groupedSampleData, sampleData } from "./sampleData.js";

const metadata: Meta<SearchSelectMenu> = {
    title: "Elements / Search Select / Tethered Menu",
    component: "ak-search-select-menu",
    parameters: {
        docs: {
            description: {
                component: "The tethered panel containing the scrollable list of selectable items",
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

const onClick = (event: SearchSelectSelectMenuEvent) => {
    const target = document.querySelector("#action-button-message-pad");
    target!.innerHTML = "";
    target!.append(
        new DOMParser().parseFromString(`<li>${event.value}</li>`, "text/xml").firstChild!,
    );
};

const container = (testItem: TemplateResult) => {
    window.setTimeout(() => {
        const menu = document.getElementById("ak-search-select-menu");
        const container = document.getElementById("the-main-event");
        if (menu && container) {
            container.addEventListener("ak-search-select-select-menu", onClick);
            (menu as SearchSelectMenu).host = container;
        }
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
        <div id="the-answer-block">
            <p>Messages received from the menu:</p>
            <ul id="action-button-message-pad" style="margin-top: 1em"></ul>
        </div>
    </div>`;
};

type Story = StoryObj;

const goodForYouPairs = {
    grouped: false,
    options: sampleData.slice(0, 20).map(({ produce }) => [slug(produce), produce]),
};

export const Default: Story = {
    render: () =>
        container(
            html` <ak-search-select-menu
                id="ak-search-select-menu"
                style="top: 1em; left: 1em"
                .options=${goodForYouPairs}
            ></ak-search-select-menu>`,
        ),
};

const longGoodForYouPairs = {
    grouped: false,
    options: sampleData.map(({ produce }) => [slug(produce), produce]),
};

export const Scrolling: Story = {
    render: () =>
        container(
            html` <ak-search-select-menu
                id="ak-search-select-menu"
                style="top: 1em; left: 1em"
                .options=${longGoodForYouPairs}
                .host=${document}
            ></ak-search-select-menu>`,
        ),
};

export const Grouped: Story = {
    render: () =>
        container(
            html` <ak-search-select-menu
                id="ak-search-select-menu"
                style="top: 1em; left: 1em"
                .options=${groupedSampleData}
                .host=${document}
            ></ak-search-select-menu>`,
        ),
};
