import { authentikVersionContext } from "@goauthentik/elements/AuthentikContexts";
import type { AbstractConstructor } from "@goauthentik/elements/types.js";

import { consume } from "@lit/context";
import type { LitElement } from "lit";

import type { Version } from "@goauthentik/api";

export function WithVersion<T extends AbstractConstructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithBrandProvider extends superclass {
        @consume({ context: authentikVersionContext, subscribe })
        public version!: Version;
    }
    return WithBrandProvider;
}
