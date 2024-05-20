import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-text-input";
import AkTextInput from "../ak-text-input";

const metadata: Meta<AkTextInput> = {
    title: "Components / Text Input",
    component: "ak-text-input",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for text input",
            },
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #000; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>

        ${testItem}

        <ul id="text-message-pad" style="color: #fff; margin-top: 1em"></ul>
    </div>`;

export const TextInput = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById("text-message-pad")!.innerText = `Value selected: ${JSON.stringify(
            ev.target.value,
            null,
            2,
        )}`;
    };

    return container(
        html`<ak-text-input
            @input=${displayChange}
            label="Test Text Input"
            name="ak-test-text-input"
            help="This is where you would read the help messages"
        ></ak-text-input>`,
    );
};
