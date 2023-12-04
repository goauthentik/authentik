import { createContext } from "@lit-labs/context";

import type { Config, CurrentTenant as CurrentBrand, Version } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export const authentikBrandContext = createContext<CurrentBrand>(Symbol("authentik-brand-context"));

export const authentikVersionContext = createContext<Version>(Symbol("authentik-version-context"));

export default authentikConfigContext;
