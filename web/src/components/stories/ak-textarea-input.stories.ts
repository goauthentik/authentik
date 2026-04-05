import "#elements/messages/MessageContainer";
import "../ak-textarea-input.js";

import AkTextareaInput from "../ak-textarea-input.js";

import { Meta } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<AkTextareaInput> = {
    title: "Components / Textarea Input",
    component: "ak-textarea-input",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for textarea input",
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

        <ul id="textarea-message-pad" style="color: #fff; margin-top: 1em"></ul>
    </div>`;

export const TextareaInput = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById("textarea-message-pad")!.innerText =
            `Value selected: ${JSON.stringify(ev.target.value, null, 2)}`;
    };

    return container(
        html`<ak-textarea-input
            @input=${displayChange}
            label="Test Textarea Input"
            name="ak-test-textarea-input"
            help="This is where you would read the help messages"
        ></ak-textarea-input>`,
    );
};
