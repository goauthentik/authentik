import { createContext } from "@lit-labs/context";

import { WizardState } from "./types";

export const applicationWizardContext = createContext<WizardState>(
    Symbol("ak-application-wizard-state-context"),
);
export default applicationWizardContext;
