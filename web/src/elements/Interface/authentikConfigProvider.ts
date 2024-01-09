import { authentikConfigContext } from "@goauthentik/elements/AuthentikContexts";

import { consume } from "@lit-labs/context";
import type { LitElement } from "lit";

import type { Config } from "@goauthentik/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = object> = new (...args: any[]) => T;

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
