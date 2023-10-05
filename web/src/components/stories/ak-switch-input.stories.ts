import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

// Necessary because we're NOT supplying the CSS for the interiors
// in our "light" dom.
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";

import "../ak-switch-input";
import AkSwitchInput from "../ak-switch-input";

const metadata: Meta<AkSwitchInput> = {
    title: "Components / Switch Input",
    component: "ak-switch-input",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for a switch-like toggle",
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
                        ${PFSwitch};
        </style>

        ${testItem}

        <ul id="switch-message-pad" style="margin-top: 1em"></ul>
    </div>`;

export const SwitchInput = () => {
    const result = "";

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById(
            "switch-message-pad",
        )!.innerText = `Value selected: ${JSON.stringify(ev.target.checked, null, 2)}`;
    };

    return container(
        html`<ak-switch-input
                @input=${displayChange}
                name="ak-test-switch-input"
                label="Test Switch Toggle"
                help="This is where you would read the help messages"
            ></ak-switch-input>
            <div>${result}</div>`,
    );
};
