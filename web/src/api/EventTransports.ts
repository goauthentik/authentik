import { DefaultClient, QueryArguments, AKResponse } from "./Client";

export class Transport {
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

    static list(filter?: QueryArguments): Promise<AKResponse<Transport>> {
        return DefaultClient.fetch<AKResponse<Transport>>(["events", "transports"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/events/transports/${rest}`;
    }
}
