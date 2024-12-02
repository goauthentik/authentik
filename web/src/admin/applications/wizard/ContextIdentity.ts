import { createContext } from "@lit/context";

import { LocalTypeCreate } from "./auth-method-choice/ak-application-wizard-authentication-method-choice.choices.js";
import { ApplicationWizardState } from "./types";

export const applicationWizardContext = createContext<ApplicationWizardState>(
    Symbol("ak-application-wizard-state-context"),
);

export const applicationWizardProvidersContext = createContext<LocalTypeCreate[]>(
    Symbol("ak-application-wizard-providers-context"),
);
