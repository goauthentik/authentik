/**
 * These are the navigation commands that the frame will send up to the controller. In the
 * accompanying file, `./commonWizardButtons.ts`, you'll find a variety of Next, Back, Close,
 * Cancel, and Submit buttons that can be used to send these, but these commands are also used by
 * the breadcrumbs to hop around the wizard (if the wizard client so chooses to allow),
 */

// "Kind" here is used mostly to distinguish the CSS type for the button.

export type DisabledWizardButton =
    | { kind: "next"; label?: string; disabled: true }
    | { kind: "back"; label?: string; disabled: true }
    | { kind: "close"; label?: string; disabled: true }
    | { kind: "cancel"; label?: string; disabled: true };

export type EnabledWizardButton =
    | { kind: "next"; label?: string; destination: string }
    | { kind: "back"; label?: string; destination: string }
    | { kind: "close"; label?: string }
    | { kind: "cancel"; label?: string };

export type WizardButton = DisabledWizardButton | EnabledWizardButton;

export type NavigableButton = Extract<WizardButton, { destination: string }>;

export type ButtonKind = Extract<WizardButton["kind"], PropertyKey>;

/**
 * Objects of this type are produced by the Controller, and are used in the Breadcrumbs to indicate
 * the name of the step, whether or not it is the current step ("active"), and whether or not it is
 * disabled. It is up to WizardClients to ensure that a step is not both "active" and "disabled".
 */

export type WizardStepLabel = {
    label: string;
    id: string;
    active: boolean;
    disabled: boolean;
};
