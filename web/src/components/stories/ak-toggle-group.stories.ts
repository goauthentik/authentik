import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-toggle-group";
import AkToggleGroup from "../ak-toggle-group";

const metadata: Meta<AkToggleGroup> = {
    title: "Components / Toggle Group",
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

const LIGHT = "pf-t-light";
function injectTheme() {
    setTimeout(() => {
        if (!document.body.classList.contains(LIGHT)) {
            document.body.classList.add(LIGHT);
        }
    });
}

const container = (testItem: TemplateResult) => {
    injectTheme();
    return html` <div style="background: #fff; padding: 2em">
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

export const ToggleGroup = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById(
            "toggle-message-pad",
        )!.innerText = `Value selected: ${ev.detail.value}`;
    };

    return container(
        html`<ak-toggle-group @ak-toggle=${displayChange}>
            ${testOptions.map(([key, label]) => html`<option value="${key}">${label}</option>`)}
        </ak-toggle-group>`,
    );
};
