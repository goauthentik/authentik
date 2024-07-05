import { authentikBrandContext } from "@goauthentik/elements/AuthentikContexts";
import type { AbstractConstructor } from "@goauthentik/elements/types.js";

import { consume } from "@lit/context";
import type { LitElement } from "lit";

import type { CurrentBrand } from "@goauthentik/api";

export function WithBrandConfig<T extends AbstractConstructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithBrandProvider extends superclass {
        @consume({ context: authentikBrandContext, subscribe })
        public brand!: CurrentBrand;
    }
    return WithBrandProvider;
}
