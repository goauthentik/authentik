import { createContext } from "@lit-labs/context";

import { type Config } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export default authentikConfigContext;
