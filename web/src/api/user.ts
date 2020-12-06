import { DefaultClient, PBResponse } from "./client";

let _globalMePromise: Promise<User>;

export class User {
    pk: number;
    username: string;
    name: string;
    is_superuser: boolean;
    email: boolean;
    avatar: string;

    constructor() {
        throw Error();
    }

    static me(): Promise<User> {
        if (!_globalMePromise) {
            _globalMePromise = DefaultClient.fetch<User>(["core", "users", "me"]);
        }
        return _globalMePromise;
    }

    static count(): Promise<number> {
        return DefaultClient.fetch<PBResponse<User>>(["core", "users"], {
            "page_size": 1
        }).then(r => {
            return r.pagination.count;
        });
    }
}
