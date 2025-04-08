import { createContext } from "@lit/context";

import type { Config, CurrentBrand, LicenseSummary, SessionUser } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export const authentikUserContext = createContext<SessionUser>(Symbol("authentik-user-context"));

export const authentikEnterpriseContext = createContext<LicenseSummary>(
    Symbol("authentik-enterprise-context"),
);

export const authentikBrandContext = createContext<CurrentBrand>(Symbol("authentik-brand-context"));

export default authentikConfigContext;
