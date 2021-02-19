import { AKResponse, DefaultClient, QueryArguments } from "./Client";
import { User } from "./Users";

export enum TokenIntent {
    INTENT_VERIFICATION = "verification",
    INTENT_API = "api",
    INTENT_RECOVERY = "recovery",
}

export class Token {

    pk: string;
    identifier: string;
    intent: TokenIntent;
    user: User;
    description: string;

    expires: number;
    expiring: boolean;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<User> {
        return DefaultClient.fetch<User>(["core", "tokens", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Token>> {
        return DefaultClient.fetch<AKResponse<Token>>(["core", "tokens"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/tokens/${rest}`;
    }

    static userUrl(rest: string): string {
        return `/-/user/tokens/${rest}`;
    }

    static getKey(identifier: string): Promise<string> {
        return DefaultClient.fetch<{ key: string }>(["core", "tokens", identifier, "view_key"]).then(
            (r) => r.key
        );
    }

}
