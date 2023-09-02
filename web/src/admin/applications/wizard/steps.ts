import { WizardStep } from "@goauthentik/components/ak-wizard-main";
import {
    BackStep,
    CancelWizard,
    NextStep,
    SubmitStep,
} from "@goauthentik/components/ak-wizard-main/commonWizardButtons";

import { html } from "lit";

import "./application/ak-application-wizard-application-details";
import "./auth-method-choice/ak-application-wizard-authentication-method-choice";
import "./commit/ak-application-wizard-commit-application";
import "./methods/ak-application-wizard-authentication-method";

type NamedStep = WizardStep & {
    id: string;
    valid: boolean;
};

export const newSteps = (): NamedStep[] => [
    {
        id: "application",
        label: "Application Details",
        render: () =>
            html`<ak-application-wizard-application-details></ak-application-wizard-application-details>`,
        disabled: false,
        valid: false,
        buttons: [NextStep, CancelWizard],
    },
    {
        id: "provider-method",
        label: "Authentication Method",
        render: () =>
            html`<ak-application-wizard-authentication-method-choice></ak-application-wizard-authentication-method-choice>`,
        disabled: false,
        valid: false,
        buttons: [NextStep, BackStep, CancelWizard],
    },
    {
        id: "provider-details",
        label: "Authentication Details",
        render: () =>
            html`<ak-application-wizard-authentication-method></ak-application-wizard-authentication-method>`,
        disabled: true,
        valid: false,
        buttons: [SubmitStep, BackStep, CancelWizard],
    },
    {
        id: "submit",
        label: "Submit New Application",
        render: () =>
            html`<ak-application-wizard-commit-application></ak-application-wizard-commit-application>`,
        disabled: true,
        valid: false,
        buttons: [BackStep, CancelWizard],
    },
];
