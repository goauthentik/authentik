import { WizardStep, makeWizardId } from "@goauthentik/components/ak-wizard-main";

import { msg } from "@lit/localize";
import { html } from "lit";

import "./application/ak-application-wizard-application-details";
import "./auth-method-choice/ak-application-wizard-authentication-method-choice";
import "./auth-method/ak-application-wizard-authentication-method";

export const steps: WizardStep[] = [
    {
        id: makeWizardId("application"),
        nextStep: makeWizardId("auth-method-choice"),
        label: "Application Details",
        renderer: () =>
            html`<ak-application-wizard-application-details></ak-application-wizard-application-details>`,
        disabled: false,
        nextButtonLabel: msg("Next"),
        valid: true,
    },
    {
        id: makeWizardId("auth-method-choice"),
        backStep: makeWizardId("application"),
        nextStep: makeWizardId("auth-method"),
        label: "Authentication Method",
        renderer: () =>
            html`<ak-application-wizard-authentication-method-choice></ak-application-wizard-authentication-method-choice>`,
        disabled: false,
        nextButtonLabel: msg("Next"),
        backButtonLabel: msg("Back"),
        valid: true,
    },
    {
        id: makeWizardId("auth-method"),
        backStep: makeWizardId("auth-method-choice"),
        label: "Authentication Details",
        renderer: () =>
            html`<ak-application-wizard-authentication-method></ak-application-wizard-authentication-method>`,
        disabled: true,
        nextButtonLabel: msg("Submit"),
        backButtonLabel: msg("Back"),
        valid: true,
    },
];
