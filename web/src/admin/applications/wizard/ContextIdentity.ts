import { createContext } from "@lit/context";

import { ApplicationWizardState } from "./types";

export const applicationWizardContext = createContext<ApplicationWizardState>(
    Symbol("ak-application-wizard-state-context"),
);

export default applicationWizardContext;
