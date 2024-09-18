export type DisabledWizardButton =
    | { kind: "back"; label?: string; disabled: true }
    | { kind: "cancel"; label?: string; disabled: true }
    | { kind: "close"; label?: string; disabled: true }
    | { kind: "next"; label?: string; disabled: true };

export type EnabledWizardButton =
    | { kind: "back"; label?: string; destination: string }
    | { kind: "cancel"; label?: string }
    | { kind: "close"; label?: string }
    | { kind: "next"; label?: string; destination: string };

export type WizardButton = DisabledWizardButton | EnabledWizardButton;

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
