import type { WizardStepState } from "./types.js";

import { createContext } from "@lit/context";

export const wizardStepContext = createContext<WizardStepState>(
    Symbol.for("authentik-wizard-step-labels"),
);
