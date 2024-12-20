import { createContext } from "@lit/context";

import type { WizardStepState } from "./types";

export const wizardStepContext = createContext<WizardStepState>(
    Symbol("authentik-wizard-step-labels"),
);
