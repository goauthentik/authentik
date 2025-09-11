import { LocalTypeCreate } from "./steps/ProviderChoices.js";

import { createContext } from "@lit/context";

export const applicationWizardProvidersContext = createContext<LocalTypeCreate[]>(
    Symbol.for("ak-application-wizard-providers-context"),
);
