import { TemplateResult } from "lit";

export type WizardNavCommand = "next" | "back" | "close" | ["goto", number];

// The label of the button, the command the button should execute, and if the button
// should be marked "disabled."
export type WizardButton = [string, WizardNavCommand, boolean?];

export interface WizardStep {
    // The name of the step, as shown in the navigation.
    label: string;

    // A function which returns the html for rendering the actual content of the step, its form and
    // such.
    render: () => TemplateResult;

    // A collection of buttons, in render order, that are to be shown in the button bar. The
    // semantics of the buttons are simple: 'next' will navigate to currentStep + 1, 'back' will
    // navigate to currentStep - 1, 'close' will close the window, and ['goto', number] will
    // navigate to a specific step in order.
    //
    // It is possible for the controlling component that wraps ak-wizard-main to supply a modified
    // collection of steps at any time, thus altering the behavior of future steps, or providing a
    // tree-like structure to the wizard.
    //
    // Note that if you change the steps radically (inserting some in front of the currentStep,
    // which is something you should never, ever do... never, ever make the customer go backward to
    // solve a problem that was your responsibility. "Going back" to fix their own mistakes is, of
    // course, their responsibility) you may have to set the currentStep as well.
    buttons: WizardButton[];

    // If this step is "disabled," the prior step's next button will be disabled.
    disabled: boolean;
}

export interface WizardPanel extends HTMLElement {
    validator?: () => boolean;
}
