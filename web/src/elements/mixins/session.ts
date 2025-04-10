import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { UIConfig, getConfigForUser } from "@goauthentik/common/ui/config";
import { refreshMe } from "@goauthentik/common/users";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";
import { createMixin } from "@goauthentik/elements/utils/mixins";

import { consume, createContext } from "@lit/context";
import { Context, ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import type { SessionUser } from "@goauthentik/api";

export interface SessionConsumer {
    /**
     * The current session user of the application.
     */
    session?: SessionUser;
    /**
     * The UI configuration of the application.
     */
    uiConfig?: UIConfig;
}

export const authentikSessionContext = createContext<SessionUser>(
    Symbol("authentik-session-context"),
);

export const authentikUIConfigContext = createContext<UIConfig>(
    Symbol("authentik-session-context"),
);

export class SessionController implements ReactiveController {
    readonly #host: ReactiveElementHost<SessionConsumer>;
    readonly #sessionContext: ContextProvider<Context<unknown, SessionUser | undefined>>;
    readonly #uiConfigContext: ContextProvider<Context<unknown, UIConfig | undefined>>;

    constructor(host: ReactiveElementHost<SessionConsumer>) {
        this.#host = host;

        this.#sessionContext = new ContextProvider(this.#host, {
            context: authentikSessionContext,
            initialValue: undefined,
        });

        this.#uiConfigContext = new ContextProvider(this.#host, {
            context: authentikUIConfigContext,
            initialValue: undefined,
        });

        this.refresh();
    }

    public readonly refresh = async () => {
        const session = await refreshMe();
        this.#sessionContext.setValue(session);
        this.#uiConfigContext.setValue(getConfigForUser(session.user));

        this.#host.session = session;
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostUpdate() {
        // If the Interface changes its config information, we should notify all
        // users of the context of that change, without creating an infinite
        // loop of resets.

        if (this.#host.session !== this.#sessionContext.value) {
            this.#sessionContext.setValue(this.#host.session);
            this.#uiConfigContext.setValue(getConfigForUser(this.#host.session?.user));
        }
    }
}

/**
 * A mixin that provides the application session to the element.
 *
 * @category Mixin
 */
export const WithSession = createMixin<SessionConsumer>(
    ({
        /**
         * The superclass constructor to extend.
         */
        SuperClass,
        /**
         * Whether or not to subscribe to the context.
         */
        subscribe = true,
    }) => {
        abstract class AKSessionProvider extends SuperClass implements SessionConsumer {
            @consume({
                context: authentikSessionContext,
                subscribe,
            })
            public session!: SessionUser;

            @consume({
                context: authentikUIConfigContext,
                subscribe,
            })
            public uiConfig!: UIConfig;
        }

        return AKSessionProvider;
    },
);
