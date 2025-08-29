import "#elements/messages/MessageContainer";
import "../ak-multi-select.js";

import AkMultiSelect from "../ak-multi-select.js";

import { Meta } from "@storybook/web-components";

import { html, render, TemplateResult } from "lit";

const metadata: Meta<AkMultiSelect> = {
    title: "Components / MultiSelect",
    component: "ak-multi-select",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for multi-select displays",
            },
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

        ${testItem}

        <div id="message-pad" style="margin-top: 1em"></div>
    </div>`;

const testOptions = [
    ["funky", "Option One: Funky"],
    ["strange", "Option Two: Strange"],
    ["weird", "Option Three: Weird"],
];

export const RadioInput = () => {
    const result = "";

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        const messagePad = document.getElementById("message-pad");
        const component: AkMultiSelect | null = document.querySelector(
            'ak-multi-select[name="ak-test-multi-select"]',
        );

        const results = html`
            <p>Results from event:</p>
            <ul style="list-style-type: disc">
                ${ev.target.value.map((v: string) => html`<li>${v}</li>`)}
            </ul>
            <p>Results from component:</p>
            <ul style="list-style-type: disc">
                ${component!.json().map((v: string) => html`<li>${v}</li>`)}
            </ul>
        `;

        render(results, messagePad!);
    };

    return container(
        html`<ak-multi-select
                @ak-select=${displayChange}
                label="Test Radio Button"
                name="ak-test-multi-select"
                help="This is where you would read the help messages"
                .options=${testOptions}
            ></ak-multi-select>
            <div>${result}</div>`,
    );
};
