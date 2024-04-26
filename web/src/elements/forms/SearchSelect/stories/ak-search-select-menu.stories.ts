import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { TemplateResult, html } from "lit";

import "../ak-search-select-menu.js";
import { SearchSelectClickEvent, SearchSelectMenu } from "../ak-search-select-menu.js";
import { sampleData } from "./sampleData.js";

const metadata: Meta<AkDualSelectAvailablePane> = {
    title: "Elements / Search Select / Items Menu",
    component: "ak-search-select-menu",
    parameters: {
        docs: {
            description: {
                component: "The panel containing the scrollable list of selectable items",
            },
        },
    },
    argTypes: {
        options: {
            type: "string",
            description: "An array of [key, label, desc] pairs of what to show",
        },
        selected: {
            type: "string",
            description: "The key of a default selected item",
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #fff; padding: 2em; position: relative">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
            #the-answer-block {
                padding-top: calc(50vh + 3em);
            }
        </style>
        <ak-message-container></ak-message-container>
        ${testItem}
        <div id="the-answer-block">
            <p>Messages received from the menu:</p>
            <ul id="action-button-message-pad" style="margin-top: 1em"></ul>
        </div>
    </div>`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onClick = (event: SearchSelectClickEvent) => {
    const target = document.querySelector("#action-button-message-pad");
    target!.innerHTML = "";
    target!.append(
        new DOMParser().parseFromString(`<li>${event.value}</li>`, "text/xml").firstChild!,
    );
};

window.addEventListener(SearchSelectClickEvent.EVENT_NAME, onClick);

type Story = StoryObj;

const goodForYouPairs = {
    grouped: false,
    options: sampleData.slice(0, 20).map(({ produce }) => [slug(produce), produce]),
};

export const Default: Story = {
    render: () =>
        container(
            html` <ak-search-select-menu
                style="top: 1em; left: 1em"
                .options=${goodForYouPairs}
                .host=${document}
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
                style="top: 1em; left: 1em"
                .options=${longGoodForYouPairs}
                .host=${document}
            ></ak-search-select-menu>`,
        ),
};

const groupedSampleData = (() => {
    const seasoned = sampleData.reduce(
        (acc, { produce, seasons, desc }) => [
            ...acc,
            ...seasons.map((season) => [season, produce, desc]),
        ],
        [],
    );
    const grouped = Object.groupBy(seasoned, ([season]) => season);
    return {
        grouped: true,
        options: ["Spring", "Summer", "Fall", "Winter"].map((season) => ({
            name: season,
            options: grouped[season],
        })),
    };
})();

export const Grouped: Story = {
    render: () =>
        container(
            html` <ak-search-select-menu
                style="top: 1em; left: 1em"
                .options=${groupedSampleData}
                .host=${document}
            ></ak-search-select-menu>`,
        ),
};
