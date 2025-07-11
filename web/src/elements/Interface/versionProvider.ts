import { authentikVersionContext } from "@goauthentik/elements/AuthentikContexts";

import { consume } from "@lit/context";
import { Constructor } from "@lit/reactive-element/decorators/base.js";
import type { LitElement } from "lit";

import type { Version } from "@goauthentik/api";

/**
 * A consumer that provides version information to the element.
 */
export declare class VersionConsumer {
    /**
     * The current version of the application.
     */
    public readonly version: Version;
}

export function WithVersion<T extends Constructor<LitElement>>(
    /**
     * The superclass constructor to extend.
     */
    SuperClass: T,
    /**
     * Whether or not to subscribe to the context.
     */
    subscribe = true,
) {
    class VersionProvider extends SuperClass {
        @consume({ context: authentikVersionContext, subscribe })
        public version!: Version;
    }

    return VersionProvider as Constructor<VersionConsumer> & T;
}
