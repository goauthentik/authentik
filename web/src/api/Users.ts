import { CoreApi, User } from "authentik-api";
import { DEFAULT_CONFIG } from "./Config";

let _globalMePromise: Promise<User>;
export function me(): Promise<User> {
    if (!_globalMePromise) {
        _globalMePromise = new CoreApi(DEFAULT_CONFIG).coreUsersMe({});
    }
    return _globalMePromise;
}
