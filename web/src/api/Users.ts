import { CoreApi } from "./apis";
import { DEFAULT_CONFIG } from "./Config";
import { User } from "./models";

let _globalMePromise: Promise<User>;
export function me(): Promise<User> {
    if (!_globalMePromise) {
        _globalMePromise = new CoreApi(DEFAULT_CONFIG).coreUsersMe({});
    }
    return _globalMePromise;
}
