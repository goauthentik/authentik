import { authentikTenantContext } from "@goauthentik/elements/AuthentikContexts.js";

import { consume } from "@lit-labs/context";
import type { LitElement } from "lit";

import type { CurrentTenant } from "@goauthentik/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T extends LitElement> = { new (...args: any[]): T };

export interface WithTenantConfigInterface {
    tenant: CurrentTenant;
}

type WithTenantConfigReturn = abstract new (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ...args: any[]
) => LitElement & WithTenantConfigInterface;

export function WithTenantConfig<T extends Constructor<LitElement>>(
    superclass: T,
    subscribe = true,
): T & WithTenantConfigReturn {
    abstract class WithTenantProvider extends superclass {
        @consume({ context: authentikTenantContext, subscribe })
        public tenant!: CurrentTenant;
    }
    return WithTenantProvider;
}
