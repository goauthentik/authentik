import "#elements/messages/MessageContainer";
import "../ak-dual-select.js";

import { AkDualSelect } from "../ak-dual-select.js";

import { Meta, StoryObj } from "@storybook/web-components";
import { kebabCase } from "change-case";

import { html, TemplateResult } from "lit";

const metadata: Meta<AkDualSelect> = {
    title: "Elements / Dual Select / Dual Select",
    component: "ak-dual-select",
    parameters: {
        docs: {
            description: {
                component: "The three-panel assembly",
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
        pages: {
            type: "string",
            description: "An authentik pagination object.",
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
const handleMoveChanged = (result: any) => {
    const target = document.querySelector("#action-button-message-pad");
    target!.innerHTML = "";
    result.detail.value.forEach((key: string) => {
        target!.append(new DOMParser().parseFromString(`<li>${key}</li>`, "text/xml").firstChild!);
    });
};

window.addEventListener("change", handleMoveChanged);

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

const goodForYouPairs = goodForYou.map((key) => [kebabCase(key), key]);

export const Default: Story = {
    render: () => container(html` <ak-dual-select .options=${goodForYouPairs}></ak-dual-select>`),
};
