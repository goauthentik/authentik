import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { TemplateResult, html } from "lit";

import "../components/ak-dual-select-available-pane";
import { AkDualSelectAvailablePane } from "../components/ak-dual-select-available-pane";
import { DualSelectMoveSelectedEvent } from "../events";
import "./sb-host-provider";

const metadata: Meta<AkDualSelectAvailablePane> = {
    title: "Elements / Dual Select / Available Items Pane",
    component: "ak-dual-select-available-pane",
    parameters: {
        docs: {
            description: {
                component: "The vertical panel separating two dual-select elements.",
            },
        },
    },
    argTypes: {
        options: {
            type: "string",
            description: "An array of [key, label] pairs of what to show",
        },
        selected: {
            type: "string",
            description: "An array of [key] of what has already been selected",
        },
        toMove: {
            type: "string",
            description: "An array of items which are to be moved to the receiving pane.",
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
        <sb-dual-select-host-provider> ${testItem} </sb-dual-select-host-provider>
        <p>Messages received from the button:</p>
        <ul id="action-button-message-pad" style="margin-top: 1em"></ul>
    </div>`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleMoveChanged = (result: DualSelectMoveSelectedEvent) => {
    const target = document.querySelector("#action-button-message-pad");
    target!.innerHTML = "";
    result.keys.forEach((key: string) => {
        target!.append(new DOMParser().parseFromString(`<li>${key}</li>`, "text/xml").firstChild!);
    });
};

window.addEventListener(DualSelectMoveSelectedEvent.eventName, handleMoveChanged);

type Story = StoryObj;

const goodForYou = [
    "Apple",
    "Arrowroot",
    "Artichoke",
    "Arugula",
    "Asparagus",
    "Avocado",
    "Bamboo",
    "Banana",
    "Basil",
    "Beet Root",
    "Blackberry",
    "Blueberry",
    "Bok Choy",
    "Broccoli",
    "Brussels sprouts",
    "Cabbage",
    "Cantaloupes",
    "Carrot",
    "Cauliflower",
];

const goodForYouPairs = goodForYou.map((key) => [slug(key), key]);

export const Default: Story = {
    render: () =>
        container(
            html` <ak-dual-select-available-pane
                .options=${goodForYouPairs}
            ></ak-dual-select-available-pane>`,
        ),
};

const someSelected = new Set([
    goodForYouPairs[2][0],
    goodForYouPairs[8][0],
    goodForYouPairs[14][0],
]);

export const SomeSelected: Story = {
    render: () =>
        container(
            html` <ak-dual-select-available-pane
                .options=${goodForYouPairs}
                .selected=${someSelected}
            ></ak-dual-select-available-pane>`,
        ),
};
