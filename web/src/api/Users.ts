import { CoreApi, SessionUser } from "authentik-api";
import { DEFAULT_CONFIG } from "./Config";

let _globalMePromise: Promise<SessionUser>;
export function me(): Promise<SessionUser> {
    if (!_globalMePromise) {
        _globalMePromise = new CoreApi(DEFAULT_CONFIG).coreUsersMe({});
    }
    return _globalMePromise;
}
