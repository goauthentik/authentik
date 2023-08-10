import { TemplateResult } from "lit";

type PhantomType<Type, Data> = { _type: Type } & Data;

export type WizardStepId = PhantomType<"WizardId", string>;

export const makeWizardId = (id: string): WizardStepId => id as WizardStepId;

export interface WizardStep {
    id: WizardStepId;
    nextStep?: WizardStepId;
    backStep?: WizardStepId;
    label: string;
    valid: boolean;
    renderer: () => TemplateResult;
    disabled: boolean;
    nextButtonLabel?: string;
    backButtonLabel?: string;
}
