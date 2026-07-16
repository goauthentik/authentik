/**
 * @file Storybook stories for the default ToggleGroup component implementation
 */

import "#elements/messages/MessageContainer";
import "../ToggleGroup";

import { ToggleGroup, ToggleGroupEvent } from "../ToggleGroup";

import { Meta } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<ToggleGroup> = {
    title: "Elements / Toggle Group",
    component: "ak-toggle-group",
    parameters: {
        docs: {
            description: {
                component: "A stylized toggle control",
            },
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) => {
    return html` <div style="padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        ${testItem}
        <ul id="toggle-message-pad" style="margin-top: 1em"></ul>
    </div>`;
};

const testOptions = [
    ["funky", "Option One: The Funky One"],
    ["invalid", "Option Two: The Invalid One"],
    ["weird", "Option Three: The Weird One"],
];

export const Default = () => {
    const displayChange = (ev: ToggleGroupEvent) => {
        document.getElementById("toggle-message-pad")!.innerText = `Value selected: ${ev.value}`;
    };

    return container(
        html`<ak-toggle-group @ak-toggle=${displayChange}>
            ${testOptions.map(([key, label]) => html`<option value="${key}">${label}</option>`)}
        </ak-toggle-group>`,
    );
};

export const Compact = () => {
    const displayChange = (ev: ToggleGroupEvent) => {
        document.getElementById("toggle-message-pad")!.innerText = `Value selected: ${ev.value}`;
    };

    return container(
        html`<ak-toggle-group compact @ak-toggle=${displayChange}>
            ${testOptions.map(([key, label]) => html`<option value="${key}">${label}</option>`)}
        </ak-toggle-group>`,
    );
};
