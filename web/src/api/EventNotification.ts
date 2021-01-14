import { DefaultClient, QueryArguments, PBResponse } from "./Client";

export class Notification {
    pk: string;
    name: string;
    mode: string;
    mode_verbose: string;
    webhook_url: string;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Transport> {
        return DefaultClient.fetch<Transport>(["events", "transports", pk]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Transport>> {
        return DefaultClient.fetch<PBResponse<Transport>>(["events", "transports"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/events/transports/${rest}`;
    }
}
