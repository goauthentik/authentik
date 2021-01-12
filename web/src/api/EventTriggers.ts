import { DefaultClient, QueryArguments, PBResponse } from "./Client";

export class Trigger {
    pk: string;
    name: string;
    transports: string[];
    severity: string;
    group?: string;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Trigger> {
        return DefaultClient.fetch<Trigger>(["events", "triggers", pk]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Trigger>> {
        return DefaultClient.fetch<PBResponse<Trigger>>(["events", "triggers"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/events/triggers/${rest}`;
    }
}
