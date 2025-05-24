import { createContext } from "@lit/context";

import type { WizardStepState } from "./types.js";

export const wizardStepContext = createContext<WizardStepState>(
    Symbol("authentik-wizard-step-labels"),
);
