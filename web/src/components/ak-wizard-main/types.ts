import { type LitElement, type ReactiveControllerHost, type TemplateResult } from "lit";

/** These are the navigation commands that the frame will send up to the controller. In the
 * accompanying file, `./commonWizardButtons.ts`, you'll find a variety of Next, Back, Close,
 * Cancel, and Submit buttons that can be used to send these, but these commands are also
 * used by the breadcrumbs to hop around the wizard (if the wizard client so chooses to allow),
 */

export type WizardNavCommand =
    | { command: "next" }
    | { command: "back" }
    | { command: "close" }
    | { command: "goto"; step: number };

/**
 * The pattern for buttons being passed to the wizard.  See `./commonWizardButtons.ts` for
 * example implementations.  The details are: Label, Command, and Disabled.
 */
export type WizardButton = [string, WizardNavCommand, boolean?];

/**
 * Objects of this type are produced by the Controller, and are used in the Breadcrumbs to
 * indicate the name of the step, whether or not it is the current step ("active"), and
 * whether or not it is disabled.  It is up to WizardClients to ensure that a step is
 * not both "active" and "disabled".
 */

export type WizardStepLabel = {
    label: string;
    index: number;
    active: boolean;
    disabled: boolean;
};

type LitControllerHost = ReactiveControllerHost & LitElement;

export interface AkWizard<D> extends LitControllerHost {
    // Every wizard must provide a list of the steps to show. This list can change, but if it does,
    // note that the *first* page must never change, and it's the responsibility of the developer to
    // ensure that if the list changes that the currentStep points to the right place.
    steps: WizardStep[];

    // The index of the current step;
    currentStep: number;

    // An accessor to the current step;
    step: WizardStep;

    // Handle pressing the "close," "cancel," or "done" buttons.
    close: () => void;

    // When a navigation event such as "next," "back," or "go to" (from the breadcrumbs) occurs.
    handleNav: (_1: number | undefined) => void;

    // When a notification that the data on the live form has changed.
    handleUpdate: (_1: D) => void;
}

export interface WizardStep {
    // The name of the step, as shown in the navigation.
    label: string;

    // A function which returns the html for rendering the actual content of the step, its form and
    // such.
    render: () => TemplateResult;

    // A collection of buttons, in render order, that are to be shown in the button bar. If you can,
    // always lead with the [Back] button and ensure it's in the same place every time. The
    // controller's current behavior is to call the host's `handleNav()` command with the index of
    // the requested step, or undefined if the command is nonsensical.
    buttons: WizardButton[];

    // If this step is "disabled," the prior step's next button will be disabled.
    disabled: boolean;
}

export interface WizardPanel extends HTMLElement {
    validator?: () => boolean;
}
