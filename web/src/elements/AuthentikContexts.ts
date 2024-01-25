import { createContext } from "@lit-labs/context";

import type { Config, CurrentBrand, LicenseSummary } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export const authentikEnterpriseContext = createContext<LicenseSummary>(
    Symbol("authentik-enterprise-context"),
);

export const authentikBrandContext = createContext<CurrentBrand>(Symbol("authentik-brand-context"));

export default authentikConfigContext;
