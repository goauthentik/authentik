import { createContext } from "@lit-labs/context";

import type { Config, CurrentTenant, LicenseSummary } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export const authentikEnterpriseContext = createContext<LicenseSummary>(
    Symbol("authentik-enterprise-context"),
);

export const authentikTenantContext = createContext<CurrentTenant>(
    Symbol("authentik-tenant-context"),
);

export default authentikConfigContext;
