import type { WizardStepState } from "./types.js";

import { createContext } from "@lit/context";

export const wizardStepContext = createContext<WizardStepState>(
    Symbol("authentik-wizard-step-labels"),
);
