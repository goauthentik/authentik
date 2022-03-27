import { LitElement } from "lit";

import { WizardStep } from "./WizardStep";

export interface WizardStepContainer extends LitElement {
    steps: WizardStep[];
    currentStep?: WizardStep;

    setSteps(...steps: WizardStep[]): void;
}
