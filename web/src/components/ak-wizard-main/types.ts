import { TemplateResult } from "lit";

export interface WizardStep {
    id: string;
    label: string;
    valid: boolean;
    renderer: () => TemplateResult;
    disabled: boolean;
    nextButtonLabel?: string;
    backButtonLabel?: string;
}
