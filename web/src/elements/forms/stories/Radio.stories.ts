import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../Radio";
import Radio from "../Radio";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const metadata: Meta<Radio<any>> = {
    title: "Elements / Basic Radio",
    component: "ak-radio",
    parameters: {
        docs: {
            description: {
                component: "Our stylized radio button",
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
        <ak-message-container></ak-message-container>
        ${testItem}
        <ul id="radio-message-pad" style="margin-top: 1em"></ul>
    </div>`;

const testOptions = [
    { label: "Option One", description: html`This is option one.`, value: 1 },
    { label: "Option Two", description: html`This is option two.`, value: 2 },
    { label: "Option Three", description: html`This is option three.`, value: 3 },
];

export const BasicRadioElement = () => {
    const displayChange = (ev: InputEvent) => {
        document.getElementById("radio-message-pad")!.innerText = `Value selected: ${JSON.stringify(
            (ev.target as HTMLInputElement)!.value,
            null,
            2,
        )}`;
    };

    return container(
        html`<ak-radio
            @input=${displayChange}
            name="ak-test-radio-input"
            .options=${testOptions}
        ></ak-radio>`,
    );
};
