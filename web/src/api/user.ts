import { DefaultClient, PBResponse } from "./client";

export class User {
    pk?: number;
    username?: string;
    name?: string;
    is_superuser?: boolean;
    email?: boolean;
    avatar?: string;

    static me(): Promise<User> {
        return DefaultClient.fetch<User>(["core", "users", "me"]);
    }

    static count(): Promise<number> {
        return DefaultClient.fetch<PBResponse<User>>(["core", "users"], {
            "page_size": 1
        }).then(r => {
            return r.pagination.count;
        });
    }
}
