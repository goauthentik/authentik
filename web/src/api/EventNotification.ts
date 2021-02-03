import { DefaultClient, QueryArguments, PBResponse } from "./Client";
import { Event } from "./Events";

export class Notification {
    pk: string;
    severity: string;
    body: string;
    created: string;
    event?: Event;
    seen: boolean;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Notification> {
        return DefaultClient.fetch<Notification>(["events", "notifications", pk]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Notification>> {
        return DefaultClient.fetch<PBResponse<Notification>>(["events", "notifications"], filter);
    }

    static markSeen(pk: string): Promise<{seen: boolean}> {
        return DefaultClient.update(["events", "notifications", pk], {
            "seen": true
        });
    }

}
