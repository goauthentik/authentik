import { authentikConfigContext } from "@goauthentik/elements/AuthentikContexts";
import type { Constructor } from "@goauthentik/elements/types.js";

import { consume } from "@lit/context";
import type { LitElement } from "lit";

import type { Config } from "@goauthentik/api";

export function WithAuthentikConfig<T extends Constructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithAkConfigProvider extends superclass {
        @consume({ context: authentikConfigContext, subscribe })
        public authentikConfig!: Config;
    }
    return WithAkConfigProvider;
}
