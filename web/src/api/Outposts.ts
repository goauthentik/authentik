import { DefaultClient, AKResponse, QueryArguments } from "./Client";
import { Provider } from "./Providers";

export interface OutpostHealth {
    last_seen: number;
    version: string;
    version_should: string;
    version_outdated: boolean;
}

export class Outpost {

    pk: string;
    name: string;
    providers: number[];
    providers_obj: Provider[];
    service_connection?: string;
    _config: QueryArguments;
    token_identifier: string;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Outpost> {
        return DefaultClient.fetch<Outpost>(["outposts", "outposts", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Outpost>> {
        return DefaultClient.fetch<AKResponse<Outpost>>(["outposts", "outposts"], filter);
    }

    static health(pk: string): Promise<OutpostHealth[]> {
        return DefaultClient.fetch<OutpostHealth[]>(["outposts", "outposts", pk, "health"]);
    }

    static adminUrl(rest: string): string {
        return `/administration/outposts/${rest}`;
    }
}
