import { createContext } from "@lit/context";

import { LocalTypeCreate } from "./steps/ProviderChoices.js";

export const applicationWizardProvidersContext = createContext<LocalTypeCreate[]>(
    Symbol("ak-application-wizard-providers-context"),
);
