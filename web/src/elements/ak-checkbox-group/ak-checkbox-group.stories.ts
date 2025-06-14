import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "./ak-checkbox-group";
import { CheckboxGroup as AkCheckboxGroup } from "./ak-checkbox-group";

const metadata: Meta<AkCheckboxGroup> = {
    title: "Elements / Checkbox Group",
    component: "ak-checkbox-group",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for check buttons",
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

        <ul id="check-message-pad" style="margin-top: 1em"></ul>
    </div>`;

const testOptions = [
    { label: "Option One: funky", name: "funky" },
    { label: "Option Two: invalid", name: "invalid" },
    { label: "Option Three: weird", name: "weird" },
];

export const CheckboxGroup = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById("check-message-pad")!.innerHTML = `
<p>Values selected on target: ${ev.target.value.join(", ")}</p>
<p>Values sent in event: ${ev.detail.join(", ")}</p>
<p>Values present as data-ak-control: <kbd>${JSON.stringify(ev.target.json, null)}</kbd></p>`;
    };

    return container(
        html` <p style="max-width: 50ch; padding-bottom: 1rem;">
                Evented example. Intercept the <kbd>input</kbd> event and display the value seen in
                the event target.
            </p>

            <ak-checkbox-group
                @change=${displayChange}
                name="ak-test-check-input"
                .options=${testOptions}
            ></ak-checkbox-group>`,
    );
};

type FDType = [string, string | FormDataEntryValue];

export const FormCheckboxGroup = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        ev.preventDefault();
        const formData = new FormData(ev.target);

        const valList = Array.from(formData)
            .map(([_key, val]: FDType) => val)
            .join(", ");

        const fdList = Array.from(formData)
            .map(
                ([key, val]: FDType) =>
                    `${encodeURIComponent(key)}=${encodeURIComponent(val as string)}`,
            )
            .join("&");

        document.getElementById("check-message-pad")!.innerHTML = `
<p>Values as seen in \`form.formData\`: ${valList}</p>
<p>Values as seen in x-form-encoded format: <kbd>${fdList}</kbd></p>`;
    };

    return container(
        html`<p style="max-width: 50ch; padding-bottom: 1rem;">
                FormData example. This variant emits the same events and exhibits the same behavior
                as the above, but instead of monitoring for 'change' events on the checkbox group,
                we monitor for the user pressing the 'submit' button. What is displayed is the
                values as understood by the &lt;form&gt; object, via its internal \`formData\`
                field, to demonstrate that this component works with forms as if it were a native
                form element.
            </p>

            <form @submit=${displayChange}>
                <ak-checkbox-group
                    name="ak-test-checkgroup-input"
                    .options=${testOptions}
                ></ak-checkbox-group>
                <button type="submit" style="margin-top: 2em">
                    <em><strong>Submit</strong></em>
                </button>
            </form>`,
    );
};
