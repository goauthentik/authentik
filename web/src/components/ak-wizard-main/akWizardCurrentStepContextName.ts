import { createContext } from "@lit-labs/context";

import { WizardStep } from "./types";

export const akWizardCurrentStepContextName = createContext<WizardStep>(
    Symbol("ak-wizard-current-step"),
);

export default akWizardCurrentStepContextName;
