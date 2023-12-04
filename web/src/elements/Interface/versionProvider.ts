import { authentikVersionContext } from "@goauthentik/elements/AuthentikContexts";

import { consume } from "@lit-labs/context";
import type { LitElement } from "lit";

import type { Version } from "@goauthentik/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = object> = abstract new (...args: any[]) => T;

export function WithVersionConfig<T extends Constructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithVersionProvider extends superclass {
        @consume({ context: authentikVersionContext, subscribe })
        public version!: Version;
    }
    return WithVersionProvider;
}
