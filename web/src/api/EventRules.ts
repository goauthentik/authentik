import { DefaultClient, QueryArguments, PBResponse } from "./Client";
import { Group } from "./Groups";

export class Rule {
    pk: string;
    name: string;
    transports: string[];
    severity: string;
    group?: Group;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Rule> {
        return DefaultClient.fetch<Rule>(["events", "rules", pk]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Rule>> {
        return DefaultClient.fetch<PBResponse<Rule>>(["events", "rules"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/events/rules/${rest}`;
    }
}
