import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { isResponseErrorLike } from "@goauthentik/common/errors/network";
import {
    EVENT_LOCALE_REQUEST,
    LocaleContextEventDetail,
} from "@goauthentik/elements/ak-locale-context/events.js";

import { CoreApi, SessionUser } from "@goauthentik/api";

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
 */
export async function me(): Promise<SessionUser> {
    if (memoizedSession) return memoizedSession;

    return new CoreApi(DEFAULT_CONFIG)
        .coreUsersMeRetrieve()
        .then((nextSession) => {
            const locale: string | undefined = nextSession.user.settings.locale;

            if (locale) {
                console.debug(`authentik/locale: Activating user's configured locale '${locale}'`);

                window.dispatchEvent(
                    new CustomEvent<LocaleContextEventDetail>(EVENT_LOCALE_REQUEST, {
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
                    const { pathname, search, hash } = window.location;

                    const authFlowRedirectURL = new URL(
                        `/flows/-/default/authentication/`,
                        window.location.origin,
                    );

                    authFlowRedirectURL.searchParams.set("next", `${pathname}${search}${hash}`);

                    window.location.assign(authFlowRedirectURL);
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
