import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";

import { consume } from "@lit/context";
import { Context, ContextProvider, createContext } from "@lit/context";
import { Constructor } from "@lit/reactive-element/decorators/base.js";
import type { LitElement } from "lit";
import type { ReactiveController } from "lit";

import type { Version } from "@goauthentik/api";
import { AdminApi } from "@goauthentik/api";

/**
 * A consumer that provides version information to the element.
 */
export interface VersionConsumer {
    /**
     * The current version of the application.
     */
    version: Version;
}

export const authentikVersionContext = createContext<Version>(Symbol("authentik-version-context"));

export class VersionController implements ReactiveController {
    readonly #host: ReactiveElementHost<VersionConsumer>;
    readonly #context: ContextProvider<Context<unknown, Version | undefined>>;

    constructor(host: ReactiveElementHost<VersionConsumer>) {
        this.#host = host;
        this.#context = new ContextProvider(this.#host, {
            context: authentikVersionContext,
            initialValue: undefined,
        });

        this.refresh();
    }

    public readonly refresh = () => {
        new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve().then((version) => {
            this.#context.setValue(version);
            this.#host.version = version;
        });
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostUpdate() {
        // If the Interface changes its version information for some reason,
        // we should notify all users of the context of that change. doesn't
        if (this.#host.version !== this.#context.value) {
            this.#context.setValue(this.#host.version);
        }
    }
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
