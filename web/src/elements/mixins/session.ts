import { APIResult, isAPIResultReady } from "#common/api/responses";
import { createUIConfig, DefaultUIConfig, UIConfig } from "#common/ui/config";

import { ContextControllerRegistry } from "#elements/controllers/ContextControllerRegistry";
import { AuthentikConfigContext, kAKConfig } from "#elements/mixins/config";
import { kAKLocale, LocaleContext, LocaleContextValue } from "#elements/mixins/locale";
import { createMixin } from "#elements/types";

import { ConsoleLogger } from "#logger/browser";

import { type Config, type SessionUser, type UserSelf } from "@goauthentik/api";

import { consume, createContext } from "@lit/context";
import { property } from "lit/decorators.js";

export const kAKSessionContext = Symbol("kAKSessionContext");

/**
 * The Lit context for the session information.
 *
 * @category Context
 * @see {@linkcode SessionMixin}
 * @see {@linkcode WithSession}
 */
export const SessionContext = createContext<APIResult<SessionUser>>(
    Symbol("authentik-session-context"),
);

export type SessionContext = typeof SessionContext;

/**
 * A consumer that provides session information to the element.
 *
 * @category Mixin
 * @see {@linkcode WithSession}
 */
export interface SessionMixin {
    /**
     * The current session information.
     *
     * @see {@linkcode currentUser} for access to the current user.
     */
    readonly session: APIResult<SessionUser>;

    /**
     *
     * The current user of the session.
     *
     * If this user is impersonating another user, this will be the impersonated user.
     */
    readonly currentUser: Readonly<UserSelf> | null;

    /**
     * The original user of the session.
     *
     * If this user is impersonating another user, this will be the original user.
     */
    readonly originalUser: Readonly<UserSelf> | null;

    /**
     * The aggregate uiConfig, derived from user, brand, and instance data.
     */
    readonly uiConfig: Readonly<UIConfig>;

    /**
     * Whether the current session is impersonating another user.
     */
    readonly impersonating: boolean;

    /**
     * Refresh the current session information.
     */
    refreshSession(): Promise<SessionUser | null>;
}

/**
 * Whether the user can view the admin innterface.
 */
export function canAccessAdmin(user?: UserSelf | null) {
    return (
        user &&
        (user.isSuperuser ||
            user.systemPermissions.includes("access_admin_interface") ||
            user.pk === 0)
    );
}

// console.debug.bind(console, `authentik/session:${this.constructor.name}`);

/**
 * A mixin that provides the session information to the element.
 *
 * @category Mixin
 */
export const WithSession = createMixin<SessionMixin>(
    ({
        // ---
        SuperClass,
        subscribe = true,
    }) => {
        abstract class SessionProvider extends SuperClass implements SessionMixin {
            #logger = ConsoleLogger.prefix("session");
            #contextController = ContextControllerRegistry.get(SessionContext);

            //#region Context Consumers

            @consume({
                context: AuthentikConfigContext,
                subscribe,
            })
            public readonly [kAKConfig]!: Readonly<Config>;

            @consume({
                context: LocaleContext,
                subscribe,
            })
            public [kAKLocale]!: LocaleContextValue;

            #uiConfig: Readonly<UIConfig> = DefaultUIConfig;

            @consume({
                context: SessionContext,
            })
            @property({ attribute: false })
            public session!: APIResult<Readonly<SessionUser>>;

            //#endregion

            //#region Properties

            public get uiConfig(): Readonly<UIConfig> {
                return this.#uiConfig;
            }

            public get currentUser(): Readonly<UserSelf> | null {
                return (isAPIResultReady(this.session) && this.session.user) || null;
            }

            public get originalUser(): Readonly<UserSelf> | null {
                return (isAPIResultReady(this.session) && this.session.original) || null;
            }

            public get impersonating(): boolean {
                return !!this.originalUser;
            }

            //#endregion

            //#region Methods

            public async refreshSession(): Promise<SessionUser | null> {
                this.#logger.debug("Fetching session...");
                const nextResult = await this.#contextController?.refresh();

                if (!isAPIResultReady(nextResult)) {
                    return null;
                }

                const { settings = {} } = nextResult.user || {};

                this.#uiConfig = createUIConfig(settings);

                return nextResult;
            }

            //#endregion
        }

        return SessionProvider;
    },
);
