import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../components/ak-dual-select-controls";
import { AkDualSelectControls } from "../components/ak-dual-select-controls";

const metadata: Meta<AkDualSelectControls> = {
    title: "Elements / Dual Select / Control Panel",
    component: "ak-dual-select-controls",
    parameters: {
        docs: {
            description: {
                component: "The vertical panel separating two dual-select elements.",
            },
        },
    },
    argTypes: {
        addActive: {
            type: "boolean",
            description:
                "Highlighted if the sample panel has something to move to the result panel.",
        },
        removeActive: {
            type: "boolean",
            description:
                "Highlighted if the result panel has something to move to the sample panel.",
        },
        selectAll: {
            type: "boolean",
            description: "Enable if you want both the 'move all visible' buttons.",
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
const displayMessage = (result: any) => {
    const doc = new DOMParser().parseFromString(`<li><i>Event</i>: ${result}</li>`, "text/xml");
    const target = document.querySelector("#action-button-message-pad");
    target!.appendChild(doc.firstChild!);
};

window.addEventListener("ak-dual-select-add", () => displayMessage("add"));
window.addEventListener("ak-dual-select-remove", () => displayMessage("remove"));
window.addEventListener("ak-dual-select-add-all", () => displayMessage("add all"));
window.addEventListener("ak-dual-select-remove-all", () => displayMessage("remove all"));

type Story = StoryObj;

export const Default: Story = {
    render: () => container(html` <ak-dual-select-controls></ak-dual-select-controls>`),
};

export const AddActive: Story = {
    render: () => container(html` <ak-dual-select-controls add-active></ak-dual-select-controls>`),
};

export const RemoveActive: Story = {
    render: () =>
        container(html` <ak-dual-select-controls remove-active></ak-dual-select-controls>`),
};

export const AddAllActive: Story = {
    render: () =>
        container(
            html` <ak-dual-select-controls
                enable-select-all
                add-all-active
            ></ak-dual-select-controls>`,
        ),
};

export const RemoveAllActive: Story = {
    render: () =>
        container(
            html` <ak-dual-select-controls
                enable-select-all
                remove-all-active
            ></ak-dual-select-controls>`,
        ),
};
