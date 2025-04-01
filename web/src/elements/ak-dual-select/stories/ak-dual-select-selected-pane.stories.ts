import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { TemplateResult, html } from "lit";

import "../components/ak-dual-select-selected-pane";
import { AkDualSelectSelectedPane } from "../components/ak-dual-select-selected-pane";
import "./sb-host-provider";

const metadata: Meta<AkDualSelectSelectedPane> = {
    title: "Elements / Dual Select / Selected Items Pane",
    component: "ak-dual-select-selected-pane",
    parameters: {
        docs: {
            description: {
                component: "The vertical panel separating two dual-select elements.",
            },
        },
    },
    argTypes: {
        // @ts-expect-error TODO: Clarify why this is an error.
        options: {
            type: "string",
            description: "An array of [key, label] pairs of what to show",
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
const handleMoveChanged = (result: any) => {
    const target = document.querySelector("#action-button-message-pad");
    target!.innerHTML = "";
    result.detail.forEach((key: string) => {
        target!.append(new DOMParser().parseFromString(`<li>${key}</li>`, "text/xml").firstChild!);
    });
};

window.addEventListener("ak-dual-select-selected-move-changed", handleMoveChanged);

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
            html` <ak-dual-select-selected-pane
                .selected=${goodForYouPairs}
            ></ak-dual-select-selected-pane>`,
        ),
};
