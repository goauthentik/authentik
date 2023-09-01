import { WizardStep } from "@goauthentik/components/ak-wizard-main";
import {
    BackStep,
    CancelWizard,
    CloseWizard,
    NextStep,
    SubmitStep,
} from "@goauthentik/components/ak-wizard-main/commonWizardButtons";

import { msg } from "@lit/localize";
import { html } from "lit";

import "./application/ak-application-wizard-application-details";
import "./auth-method-choice/ak-application-wizard-authentication-method-choice";
import "./commit/ak-application-wizard-commit-application";
import "./methods/ak-application-wizard-authentication-method";

export const steps: WizardStep[] = [
    {
        id: "application",
        label: "Application Details",
        renderer: () =>
            html`<ak-application-wizard-application-details></ak-application-wizard-application-details>`,
        disabled: false,
        buttons: [NextStep, CancelWizard],
        valid: true,
    },
    {
        id: "auth-method-choice",
        label: "Authentication Method",
        renderer: () =>
            html`<ak-application-wizard-authentication-method-choice></ak-application-wizard-authentication-method-choice>`,
        disabled: false,
        buttons: [NextStep, BackStep, CancelWizard],
        valid: true,
    },
    {
        id: "auth-method",
        label: "Authentication Details",
        renderer: () =>
            html`<ak-application-wizard-authentication-method></ak-application-wizard-authentication-method>`,
        disabled: true,
        buttons: [SubmitStep, BackStep, CancelWizard],
        valid: true,
    },
    {
        id: "commit-application",
        label: "Submit New Application",
        renderer: () =>
            html`<ak-application-wizard-commit-application></ak-application-wizard-commit-application>`,
        disabled: true,
        buttons: [BackStep, CancelWizard],
        valid: true,
    },
];
