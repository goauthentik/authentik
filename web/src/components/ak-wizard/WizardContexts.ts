import { createContext } from "@lit/context";

import type { WizardStepState } from "./types";

export const wizardStepContext = createContext<WizardStepState>(
    Symbol.for("authentik-wizard-step-labels"),
);
