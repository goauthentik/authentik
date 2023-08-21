import { WizardStep } from "@goauthentik/components/ak-wizard-main";

import { msg } from "@lit/localize";
import { html } from "lit";

import "./application/ak-application-wizard-application-details";
import "./auth-method-choice/ak-application-wizard-authentication-method-choice";
import "./methods/ak-application-wizard-authentication-method";

export const steps: WizardStep[] = [
    {
        id: "application",
        label: "Application Details",
        renderer: () =>
            html`<ak-application-wizard-application-details></ak-application-wizard-application-details>`,
        disabled: false,
        nextButtonLabel: msg("Next"),
        valid: true,
    },
    {
        id: "auth-method-choice",
        label: "Authentication Method",
        renderer: () =>
            html`<ak-application-wizard-authentication-method-choice></ak-application-wizard-authentication-method-choice>`,
        disabled: false,
        nextButtonLabel: msg("Next"),
        backButtonLabel: msg("Back"),
        valid: true,
    },
    {
        id: "auth-method",
        label: "Authentication Details",
        renderer: () =>
            html`<ak-application-wizard-authentication-method></ak-application-wizard-authentication-method>`,
        disabled: true,
        nextButtonLabel: msg("Next"),
        backButtonLabel: msg("Back"),
        valid: true,
    },
    {
        id: "commit-application",
        label: "Submit New Application",
        renderer: () =>
            html`<ak-application-wizard-commit-application></ak-application-wizard-commit-application>`,
        disabled: true,
        nextButtonLabel: msg("Submit"),
        backButtonLabel: msg("Back"),
        valid: true,
    },
    
];
