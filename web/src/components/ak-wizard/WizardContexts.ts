import type { WizardStepState } from "./shared.js";

import { createContext } from "@lit/context";

export const wizardStepContext = createContext<WizardStepState>(
    Symbol("authentik-wizard-step-labels"),
);
