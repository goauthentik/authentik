import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-radio-input";
import AkRadioInput from "../ak-radio-input";

const metadata: Meta<AkRadioInput<Record<string, number>>> = {
    title: "Components / Radio Input",
    component: "ak-radio-input",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for radio buttons",
            },
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

        ${testItem}

        <ul id="radio-message-pad" style="margin-top: 1em"></ul>
    </div>`;

const testOptions = [
    { label: "Option One", description: html`This is option one.`, value: { funky: 1 } },
    { label: "Option Two", description: html`This is option two.`, value: { invalid: 2 } },
    { label: "Option Three", description: html`This is option three.`, value: { weird: 3 } },
];

export const RadioInput = () => {
    const result = "";

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById("radio-message-pad")!.innerText = `Value selected: ${JSON.stringify(
            ev.target.value,
            null,
            2,
        )}`;
    };

    return container(
        html`<ak-radio-input
                @input=${displayChange}
                label="Test Radio Button"
                name="ak-test-radio-input"
                help="This is where you would read the help messages"
                .options=${testOptions}
            ></ak-radio-input>
            <div>${result}</div>`,
    );
};
