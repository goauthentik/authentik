import { DefaultClient, QueryArguments, AKResponse } from "./Client";
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

    static list(filter?: QueryArguments): Promise<AKResponse<Rule>> {
        return DefaultClient.fetch<AKResponse<Rule>>(["events", "rules"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/events/rules/${rest}`;
    }
}
