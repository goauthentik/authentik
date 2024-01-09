import { createContext } from "@lit-labs/context";

import type { Config, CurrentBrand } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export const authentikBrandContext = createContext<CurrentBrand>(Symbol("authentik-brand-context"));

export default authentikConfigContext;
