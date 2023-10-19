import {
    BackStep,
    CancelWizard,
    CloseWizard,
    DisabledNextStep,
    NextStep,
    SubmitStep,
} from "@goauthentik/components/ak-wizard-main/commonWizardButtons";

import { html } from "lit";

import "./application/ak-application-wizard-application-details";
import "./auth-method-choice/ak-application-wizard-authentication-method-choice";
import "./commit/ak-application-wizard-commit-application";
import "./methods/ak-application-wizard-authentication-method";
import { ApplicationStep as ApplicationStepType } from "./types";

class ApplicationStep implements ApplicationStepType {
    id = "application";
    label = "Application Details";
    disabled = false;
    valid = false;
    get buttons() {
        return [this.valid ? NextStep : DisabledNextStep, CancelWizard];
    }
    render() {
        return html`<ak-application-wizard-application-details></ak-application-wizard-application-details>`;
    }
}

class ProviderMethodStep implements ApplicationStepType {
    id = "provider-method";
    label = "Provider Type";
    disabled = false;
    valid = false;

    get buttons() {
        return [BackStep, this.valid ? NextStep : DisabledNextStep, CancelWizard];
    }

    render() {
        // prettier-ignore
        return html`<ak-application-wizard-authentication-method-choice
          ></ak-application-wizard-authentication-method-choice> `;
    }
}

class ProviderStepDetails implements ApplicationStepType {
    id = "provider-details";
    label = "Provider Configuration";
    disabled = true;
    valid = false;
    get buttons() {
        return [BackStep, this.valid ? SubmitStep : DisabledNextStep, CancelWizard];
    }

    render() {
        return html`<ak-application-wizard-authentication-method></ak-application-wizard-authentication-method>`;
    }
}

class SubmitApplicationStep implements ApplicationStepType {
    id = "submit";
    label = "Submit Application";
    disabled = true;
    valid = false;

    get buttons() {
        return this.valid ? [CloseWizard] : [BackStep, CancelWizard];
    }

    render() {
        return html`<ak-application-wizard-commit-application></ak-application-wizard-commit-application>`;
    }
}

export const newSteps = (): ApplicationStep[] => [
    new ApplicationStep(),
    new ProviderMethodStep(),
    new ProviderStepDetails(),
    new SubmitApplicationStep(),
];
