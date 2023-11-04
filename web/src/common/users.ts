import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_LOCALE_REQUEST } from "@goauthentik/common/constants";

import { CoreApi, SessionUser } from "@goauthentik/api";

let globalMePromise: Promise<SessionUser> | undefined;

export function refreshMe(): Promise<SessionUser> {
    globalMePromise = undefined;
    return me();
}

export function me(): Promise<SessionUser> {
    if (!globalMePromise) {
        globalMePromise = new CoreApi(DEFAULT_CONFIG)
            .coreUsersMeRetrieve()
            .then((user) => {
                if (!user.user.settings || !("locale" in user.user.settings)) {
                    return user;
                }
                const locale = user.user.settings.locale;
                if (locale && locale !== "") {
                    console.debug(
                        `authentik/locale: Activating user's configured locale '${locale}'`,
                    );
                    window.dispatchEvent(
                        new CustomEvent(EVENT_LOCALE_REQUEST, {
                            composed: true,
                            bubbles: true,
                            detail: { locale },
                        }),
                    );
                }
                return user;
            })
            .catch(() => {
                const defaultUser: SessionUser = {
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
                return defaultUser;
            });
    }
    return globalMePromise;
}
