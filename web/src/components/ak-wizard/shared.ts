import { msg } from "@lit/localize";

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

export const isNavigable = (b: WizardButton): b is NavigableButton =>
    "destination" in b && typeof b.destination === "string" && b.destination.length > 0;

export const ButtonKindClassnameRecord = {
    next: "pf-m-primary",
    back: "pf-m-secondary",
    close: "pf-m-link",
    cancel: "pf-m-link",
} as const satisfies Record<ButtonKind, string>;

export const ButtonKindLabelRecord = {
    next: () => msg("Next"),
    back: () => msg("Back"),
    cancel: () => msg("Cancel"),
    close: () => msg("Close"),
} as const satisfies Record<ButtonKind, () => string>;
