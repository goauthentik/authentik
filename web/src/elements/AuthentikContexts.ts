import { createContext } from "@lit-labs/context";

import type { Config, CurrentTenant } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export const authentikTenantContext = createContext<CurrentTenant>(
    Symbol("authentik-tenant-context"),
);

export default authentikConfigContext;
