import { DefaultClient, AKResponse, QueryArguments } from "./Client";

let _globalMePromise: Promise<User>;

export class User {
    pk: number;
    username: string;
    name: string;
    is_superuser: boolean;
    email: boolean;
    avatar: string;
    is_active: boolean;
    last_login: number;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<User> {
        return DefaultClient.fetch<User>(["core", "users", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<User>> {
        return DefaultClient.fetch<AKResponse<User>>(["core", "users"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/users/${rest}`;
    }

    static me(): Promise<User> {
        if (!_globalMePromise) {
            _globalMePromise = DefaultClient.fetch<User>(["core", "users", "me"]);
        }
        return _globalMePromise;
    }

    static count(): Promise<number> {
        return DefaultClient.fetch<AKResponse<User>>(["core", "users"], {
            "page_size": 1
        }).then(r => {
            return r.pagination.count;
        });
    }
}
