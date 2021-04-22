import { CoreApi, SessionUser } from "authentik-api";
import { DEFAULT_CONFIG } from "./Config";

let _globalMePromise: Promise<SessionUser>;
export function me(): Promise<SessionUser> {
    if (!_globalMePromise) {
        _globalMePromise = new CoreApi(DEFAULT_CONFIG).coreUsersMe().catch((ex) => {
            const defaultUser: SessionUser = {
                user: {
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
    return _globalMePromise;
}
