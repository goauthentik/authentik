import { createContext } from "@lit/context";

import { LocalTypeCreate } from "./auth-method-choice/ak-application-wizard-authentication-method-choice.choices.js";

export const applicationWizardProvidersContext = createContext<LocalTypeCreate[]>(
    Symbol("ak-application-wizard-providers-context"),
);
