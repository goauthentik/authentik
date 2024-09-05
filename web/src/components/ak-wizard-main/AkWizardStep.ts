import { type TemplateResult, nothing } from "lit";

import { type WizardButton } from "./types";

export abstract class WizardStep {
    // The id of the step. Must be unique. Used for navigation.
    id = "";

    // The name of the step, as shown in the navigation div of the frame
    label: string = "Embarrassingly unconfigured";

    // A collection of buttons, in render order, that are to be shown in the button bar. If you can,
    // always lead with the [Back] button and ensure it's in the same place every time. The
    // controller's current behavior is to call the host's `handleNav()` command with the index of
    // the requested step, or undefined if the command is nonsensical.
    buttons: WizardButton[] = [];

    // If true, will not be shown in the navigation sidebar
    hidden = false;

    // Returns true if the current step is "valid";
    valid: boolean = false;

    // If this step is "disabled," the prior step's next button will be disabled.
    disabled: boolean = false;

    // A function which returns the html for rendering the actual content of the step, its form and
    // such.
    render(): TemplateResult | typeof nothing {
        return nothing;
    }
}
