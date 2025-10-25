export type EnabledWizardButton =
    | { kind: "back"; label?: string; destination: string }
    | { kind: "cancel"; label?: string }
    | { kind: "close"; label?: string }
    | { kind: "next"; label?: string; destination: string };

export type WizardButton = EnabledWizardButton;

export type NavigableButton = Extract<WizardButton, { destination: string }>;

export type ButtonKind = Extract<WizardButton["kind"], PropertyKey>;

export interface WizardStepLabel {
    label: string;
    id: string;
    enabled?: boolean;
}

export type WizardStepState = {
    currentStep?: string;
    stepLabels: WizardStepLabel[];
};
