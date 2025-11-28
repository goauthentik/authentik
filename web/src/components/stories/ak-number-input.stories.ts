import "#elements/messages/MessageContainer";
import "../ak-number-input.js";

import AkNumberInput from "../ak-number-input.js";

import { Meta } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<AkNumberInput> = {
    title: "Components / Number Input",
    component: "ak-number-input",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for number input",
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

        <ul id="number-message-pad" style="color: #fff; margin-top: 1em"></ul>
    </div>`;

export const NumberInput = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById("number-message-pad")!.innerText =
            `Value selected: ${JSON.stringify(ev.target.value, null, 2)}`;
    };

    return container(
        html`<ak-number-input
            @input=${displayChange}
            label="Test Number Input"
            name="ak-test-number-input"
            help="This is where you would read the help messages"
        ></ak-number-input>`,
    );
};
