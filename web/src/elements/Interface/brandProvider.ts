import { authentikBrandContext } from "@goauthentik/elements/AuthentikContexts";

import { consume } from "@lit-labs/context";
import type { LitElement } from "lit";

import type { CurrentBrand } from "@goauthentik/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = object> = abstract new (...args: any[]) => T;

export function WithBrandConfig<T extends Constructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithBrandProvider extends superclass {
        @consume({ context: authentikBrandContext, subscribe })
        public brand!: CurrentBrand;
    }
    return WithBrandProvider;
}
