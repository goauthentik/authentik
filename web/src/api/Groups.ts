import { DefaultClient, QueryArguments, AKResponse } from "./Client";
import { EventContext } from "./Events";

export class Group {

    pk: string;
    name: string;
    is_superuser: boolean;
    attributes: EventContext;
    parent?: Group;
    users: number[];

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Group> {
        return DefaultClient.fetch<Group>(["core", "groups", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Group>> {
        return DefaultClient.fetch<AKResponse<Group>>(["core", "groups"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/groups/${rest}`;
    }
}
