import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-wizard-main";
import AkWizard from "../ak-wizard-main";
import type { WizardStep } from "../types";

const metadata: Meta<AkWizard> = {
    title: "Components / Wizard / Basic",
    component: "ak-wizard-main",
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
    </div>`;

const dummySteps: WizardStep[] = [
    {
        id: "0",
        label: "Test Step1",
        renderer: () => html`<h2>This space intentionally left blank today</h2>`,
        disabled: false,
        valid: true,
        nextButtonLabel: "Next",
        backButtonLabel: undefined,
    },
    {
        id: "1",
        label: "Test Step 2",
        renderer: () => html`<h2>This space also intentionally left blank</h2>`,
        disabled: false,
        valid: true,
        nextButtonLabel: undefined,
        backButtonLabel: "Back",
    },
];

export const OnePageWizard = () => {
    return container(
        html` <ak-wizard-main .steps=${dummySteps} prompt="Start the show!"></ak-wizard-main>`,
    );
};
