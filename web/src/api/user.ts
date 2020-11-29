import { Primitive } from "lit-html/lib/parts";
import { DefaultClient } from "./client";

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
}
