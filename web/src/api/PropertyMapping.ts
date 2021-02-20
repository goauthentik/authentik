import { DefaultClient, AKResponse, QueryArguments } from "./Client";
import { TypeCreate } from "./Providers";

export class PropertyMapping {
    pk: string;
    name: string;
    expression: string;

    verbose_name: string;
    verbose_name_plural: string;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<PropertyMapping> {
        return DefaultClient.fetch<PropertyMapping>(["propertymappings", "all", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<PropertyMapping>> {
        return DefaultClient.fetch<AKResponse<PropertyMapping>>(["propertymappings", "all"], filter);
    }

    static getTypes(): Promise<TypeCreate[]> {
        return DefaultClient.fetch<TypeCreate[]>(["propertymappings", "all", "types"]);
    }

    static adminUrl(rest: string): string {
        return `/administration/property-mappings/${rest}`;
    }
}
