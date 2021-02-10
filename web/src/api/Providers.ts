import { BaseInheritanceModel, DefaultClient, AKResponse, QueryArguments } from "./Client";

export interface TypeCreate {
    name: string;
    description: string;
    link: string;
}

export class Provider implements BaseInheritanceModel {
    pk: number;
    name: string;
    authorization_flow: string;
    object_type: string;

    assigned_application_slug?: string;
    assigned_application_name?: string;

    verbose_name: string;
    verbose_name_plural: string;

    constructor() {
        throw Error();
    }

    static get(id: number): Promise<Provider> {
        return DefaultClient.fetch<Provider>(["providers", "all", id.toString()]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Provider>> {
        return DefaultClient.fetch<AKResponse<Provider>>(["providers", "all"], filter);
    }

    static getTypes(): Promise<TypeCreate[]> {
        return DefaultClient.fetch<TypeCreate[]>(["providers", "all", "types"]);
    }

    static adminUrl(rest: string): string {
        return `/administration/providers/${rest}`;
    }
}
