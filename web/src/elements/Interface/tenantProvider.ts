import { authentikTenantContext } from "@goauthentik/elements/AuthentikContexts";

import { consume } from "@lit-labs/context";
import type { LitElement } from "lit";

import type { CurrentTenant } from "@goauthentik/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = object> = abstract new (...args: any[]) => T;

export function WithTenantConfig<T extends Constructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithTenantProvider extends superclass {
        @consume({ context: authentikTenantContext, subscribe })
        public tenant!: CurrentTenant;
    }
    return WithTenantProvider;
}
