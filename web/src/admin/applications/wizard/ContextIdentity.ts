import { LocalTypeCreate } from "./steps/ProviderChoices.js";

import { createContext } from "@lit/context";

export const applicationWizardProvidersContext = createContext<LocalTypeCreate[]>(
    Symbol("ak-application-wizard-providers-context"),
);
