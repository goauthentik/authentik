import { CoreApi, SessionUser } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "./Config";

let globalMePromise: Promise<SessionUser>;
export function me(): Promise<SessionUser> {
    if (!globalMePromise) {
        globalMePromise = new CoreApi(DEFAULT_CONFIG).coreUsersMeRetrieve().catch((ex) => {
            const defaultUser: SessionUser = {
                user: {
                    pk: -1,
                    isSuperuser: false,
                    isActive: true,
                    groups: [],
                    avatar: "",
                    uid: "",
                    username: "",
                    name: ""
                }
            };
            if (ex.status === 401 || ex.status === 403) {
                window.location.assign("/");
            }
            return defaultUser;
        });
    }
    return globalMePromise;
}
