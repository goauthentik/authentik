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
    const displayChange = (event: CustomEvent<string[]>) => {
        const target = event.target as AkCheckboxGroup;

        document.getElementById("check-message-pad")!.innerHTML = /*html*/ `
        <p>
            Values selected on target: ${target.value.join(", ")}
        </p>
        <p>
            Values sent in event: ${event.detail.join(", ")}
        </p>
        <p>
            Values present as data-ak-control: <kbd>${JSON.stringify(target.json(), null)}</kbd>
        </p>
    `;
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

type FDType = [key: string, value: string | FormDataEntryValue];

export const FormCheckboxGroup = () => {
    const displayChange = (event: SubmitEvent) => {
        event.preventDefault();

        if (!(event.target instanceof HTMLFormElement)) {
            throw new Error("Expected target to be a form element");
        }

        const formData = new FormData(event.target);

        const valList = Array.from(formData.values()).join(", ");

        const fdList = Array.from(formData, ([key, val]: FDType) => {
            return `${encodeURIComponent(key)}=${encodeURIComponent(val as string)}`;
        }).join("&");

        document.getElementById("check-message-pad")!.innerHTML = /*html*/ `
            <p>
                Values as seen in ${"`form.formData`"}: ${valList}
            </p>
            <p>
                Values as seen in x-form-encoded format: <kbd>${fdList}</kbd>
            </p>
        `;
    };

    return container(
        html`<p style="max-width: 50ch; padding-bottom: 1rem;">
                FormData example. This variant emits the same events and exhibits the same behavior
                as the above, but instead of monitoring for 'change' events on the checkbox group,
                we monitor for the user pressing the 'submit' button. What is displayed is the
                values as understood by the &lt;form&gt; object, via its internal
                ${"`form.formData`"} field, to demonstrate that this component works with forms as
                if it were a native form element.
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
