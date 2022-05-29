import { CoreApi, SessionUser } from "@goauthentik/api";
import { activateLocale } from "../interfaces/locale";
import { DEFAULT_CONFIG } from "./Config";

let globalMePromise: Promise<SessionUser> | undefined;

export function refreshMe(): Promise<SessionUser> {
    globalMePromise = undefined;
    return me();
}

export function me(): Promise<SessionUser> {
    if (!globalMePromise) {
        globalMePromise = new CoreApi(DEFAULT_CONFIG).coreUsersMeRetrieve().then((user) => {
            if (!user.user.settings || !("locale" in user.user.settings)) {
                return user;
            }
            const locale = user.user.settings.locale;
            if (locale && locale !== "") {
                console.debug(`authentik/locale: Activating user's configured locale '${locale}'`);
                activateLocale(locale);
            }
            return user;
        }).catch((ex) => {
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
                }
            };
            if (ex.response.status === 401 || ex.response.status === 403) {
                window.location.assign("/");
            }
            return defaultUser;
        });
    }
    return globalMePromise;
}
