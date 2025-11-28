import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_LOCALE_REQUEST } from "#common/constants";
import { isResponseErrorLike } from "#common/errors/network";
import { UIConfig, UserDisplay } from "#common/ui/config";

import { CoreApi, SessionUser, UserSelf } from "@goauthentik/api";

import { match } from "ts-pattern";

export interface ClientSessionPermissions {
    editApplications: boolean;
    accessAdmin: boolean;
}

/**
 * The display name of the current user, according to their UI config settings.
 */
export function formatUserDisplayName(user: UserSelf | null, uiConfig?: UIConfig): string {
    if (!user) return "";

    const label = match(uiConfig?.navbar.userDisplay)
        .with(UserDisplay.username, () => user.username)
        .with(UserDisplay.name, () => user.name)
        .with(UserDisplay.email, () => user.email)
        .with(UserDisplay.none, () => null)
        .otherwise(() => user.name || user.username);

    return label || "";
}

/**
 * Whether the current session is an unauthenticated guest session.
 */
export function isGuest(user: UserSelf | null): boolean {
    return user?.pk === -1;
}

/**
 * Create a guest session for unauthenticated users.
 *
 * @see {@linkcode me} for the actual session retrieval.
 */
function createGuestSession(): SessionUser {
    const guest: SessionUser = {
        user: {
            pk: -1,
            isSuperuser: false,
            isActive: true,
            groups: [],
            avatar: "",
            uid: "",
            username: "",
            name: "",
            settings: {},
            systemPermissions: [],
        },
    };

    return guest;
}

let memoizedSession: SessionUser | null = null;

/**
 * Refresh the current user session.
 *
 * @deprecated This should be moved to the WithSession mixin.
 */
export function refreshMe(): Promise<SessionUser> {
    memoizedSession = null;
    return me();
}

/**
 * Retrieve the current user session.
 *
 * This is a memoized function, so it will only make one request per page load.
 *
 * @see {@linkcode refreshMe} to force a refresh.
 *
 * @category Session
 */
export async function me(requestInit?: RequestInit): Promise<SessionUser> {
    if (memoizedSession) return memoizedSession;

    return new CoreApi(DEFAULT_CONFIG)
        .coreUsersMeRetrieve(requestInit)
        .then((nextSession) => {
            const locale: string | undefined = nextSession.user.settings.locale;

            if (locale) {
                console.debug(`authentik/locale: Activating user's configured locale '${locale}'`);

                window.dispatchEvent(
                    new CustomEvent(EVENT_LOCALE_REQUEST, {
                        composed: true,
                        bubbles: true,
                        detail: { locale },
                    }),
                );
            }

            return nextSession;
        })
        .catch(async (error: unknown) => {
            if (isResponseErrorLike(error)) {
                const { response } = error;

                if (response.status === 401 || response.status === 403) {
                    redirectToAuthFlow();
                }
            }

            console.debug("authentik/users: Failed to retrieve user session", error);

            return createGuestSession();
        })
        .then((nextSession) => {
            memoizedSession = nextSession;
            return nextSession;
        });
}

let pendingRedirect = false;

/**
 * Redirect to the default authentication flow, preserving the current URL as "next" parameter.
 *
 * @category Session
 */
export function redirectToAuthFlow(nextPathname = "/flows/-/default/authentication/"): void {
    if (pendingRedirect) {
        console.debug("authentik/users: Redirect already pending, ");
        return;
    }

    const { pathname, search, hash } = window.location;

    const authFlowRedirectURL = new URL(nextPathname, window.location.origin);

    authFlowRedirectURL.searchParams.set("next", `${pathname}${search}${hash}`);

    pendingRedirect = true;

    console.debug(
        `authentik/users: Redirecting to authentication flow at ${authFlowRedirectURL.href}`,
    );

    window.location.assign(authFlowRedirectURL);
}
