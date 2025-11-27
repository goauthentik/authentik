import { APIResult, isAPIResultReady } from "#common/api/responses";
import { createUIConfig, DefaultUIConfig, UIConfig } from "#common/ui/config";

import { createMixin } from "#elements/types";

import type { SessionUser, UserSelf } from "@goauthentik/api";

import { consume, createContext } from "@lit/context";
import { property } from "lit/decorators.js";

/**
 * The Lit context for the application configuration.
 *
 * @category Context
 * @see {@linkcode SessionMixin}
 * @see {@linkcode WithSession}
 */
export const SessionContext = createContext<APIResult<SessionUser>>(
    Symbol.for("authentik-session-context"),
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

// uiConfig.enabledFeatures.applicationEdit && currentUser?.isSuperuser

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
            #data: APIResult<Readonly<SessionUser>> = {
                loading: true,
                error: null,
            };

            #uiConfig: Readonly<UIConfig> = DefaultUIConfig;

            @consume({
                context: SessionContext,
                subscribe,
            })
            @property({ attribute: false })
            public set session(nextResult: APIResult<SessionUser>) {
                this.#data = nextResult;
                if (isAPIResultReady(nextResult)) {
                    const { settings = {} } = nextResult.user || {};

                    this.#uiConfig = createUIConfig(settings);
                }
            }

            public get session(): APIResult<Readonly<SessionUser>> {
                return this.#data;
            }

            public get uiConfig(): Readonly<UIConfig> {
                return this.#uiConfig;
            }

            public get currentUser(): Readonly<UserSelf> | null {
                return (isAPIResultReady(this.#data) && this.#data.user) || null;
            }

            public get originalUser(): Readonly<UserSelf> | null {
                return (isAPIResultReady(this.#data) && this.#data.original) || null;
            }

            public get impersonating(): boolean {
                return !!this.originalUser;
            }
        }

        return SessionProvider;
    },
);
