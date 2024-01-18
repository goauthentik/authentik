import { msg } from "@lit/localize";

import { WizardButton } from "./types";

export const NextStep: WizardButton = [msg("Next"), { command: "next" }];

export const BackStep: WizardButton = [msg("Back"), { command: "back" }];

export const SubmitStep: WizardButton = [msg("Submit"), { command: "next" }];

export const CancelWizard: WizardButton = [msg("Cancel"), { command: "close" }];

export const CloseWizard: WizardButton = [msg("Close"), { command: "close" }];

export const DisabledNextStep: WizardButton = [msg("Next"), { command: "next" }, true];
