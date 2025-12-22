import type { TypeCreate } from "@goauthentik/api";

import { createContext } from "@lit/context";

export const applicationWizardProvidersContext = createContext<TypeCreate[]>(
    Symbol.for("ak-application-wizard-providers-context"),
);
