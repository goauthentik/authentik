export type EnabledWizardButton =
    | { kind: "back"; label?: string; destination: string }
    | { kind: "cancel"; label?: string }
    | { kind: "close"; label?: string }
    | { kind: "next"; label?: string; destination: string };

export type WizardButton = EnabledWizardButton;

export type NavigableButton = Extract<WizardButton, { destination: string }>;

export type ButtonKind = Extract<WizardButton["kind"], PropertyKey>;

export type WizardStepLabel = {
    label: string;
    id: string;
    active: boolean;
    enabled: boolean;
};

export type WizardStepState = {
    currentStep?: string;
    stepLabels: WizardStepLabel[];
};
