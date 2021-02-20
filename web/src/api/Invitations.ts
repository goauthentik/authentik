import { DefaultClient, QueryArguments, AKResponse } from "./Client";
import { EventContext } from "./Events";
import { User } from "./Users";

export class Invitation {

    pk: string;
    expires: number;
    fixed_date: EventContext;
    created_by: User;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Invitation> {
        return DefaultClient.fetch<Invitation>(["stages", "invitation", "invitations", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Invitation>> {
        return DefaultClient.fetch<AKResponse<Invitation>>(["stages", "invitation", "invitations"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/stages/invitations/${rest}`;
    }
}
