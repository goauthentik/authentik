import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-wizard-2"
import "./ak-demo-wizard";
import AkWizard from "../ak-wizard-2";

import type { WizardStep } from "../types";
import { makeWizardId } from "../types";

const metadata: Meta<AkWizard> = {
    title: "Components / Wizard / Basic",
    component: "ak-wizard-2",
    parameters: {
        docs: {
            description: {
                component: "A container for our wizard.",
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
        <p>Messages received from the button:</p>
        <ul id="action-button-message-pad" style="margin-top: 1em"></ul>
    </div>`;



const dummySteps: WizardStep[] = [
    {
        id: makeWizardId("0"),
        label: "Test Step1",
        renderer: () => html`<h2>This space intentionally left blank today</h2>`,
        disabled: false,
        valid: true,
        nextStep: makeWizardId("1"),
        nextButtonLabel: "Next",
        backButtonLabel: undefined,
    },
    {
        id: makeWizardId("1"),
        label: "Test Step 2",
        renderer: () => html`<h2>This space also intentionally left blank</h2>`,
        disabled: false,
        valid: true,
        backStep: makeWizardId("0"),
        nextButtonLabel: undefined,
        backButtonLabel: "Back",
    },
];

export const OnePageWizard = () => {
    return container(
        html` <ak-demo-wizard .steps=${dummySteps}></ak-demo-wizard>`
    );
};
