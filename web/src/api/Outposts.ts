import { DefaultClient, AKResponse, QueryArguments } from "./Client";
import { Provider, TypeCreate } from "./Providers";

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

export interface OutpostServiceConnectionState {
    version: string;
    healthy: boolean;
}

export class OutpostServiceConnection {
    pk: string;
    name: string;
    local: boolean;
    object_type: string;
    verbose_name: string;
    verbose_name_plural: string;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<OutpostServiceConnection> {
        return DefaultClient.fetch<OutpostServiceConnection>(["outposts", "service_connections", "all", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<OutpostServiceConnection>> {
        return DefaultClient.fetch<AKResponse<OutpostServiceConnection>>(["outposts", "service_connections", "all"], filter);
    }

    static state(pk: string): Promise<OutpostServiceConnectionState> {
        return DefaultClient.fetch<OutpostServiceConnectionState>(["outposts", "service_connections", "all", pk, "state"]);
    }

    static getTypes(): Promise<TypeCreate[]> {
        return DefaultClient.fetch<TypeCreate[]>(["outposts", "service_connections", "all", "types"]);
    }

    static adminUrl(rest: string): string {
        return `/administration/outpost_service_connections/${rest}`;
    }

}
