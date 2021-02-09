import { BaseInheritanceModel, DefaultClient, AKResponse, QueryArguments } from "./Client";

export class Source implements BaseInheritanceModel {
    pk: string;
    name: string;
    slug: string;
    enabled: boolean;
    authentication_flow: string;
    enrollment_flow: string;

    constructor() {
        throw Error();
    }
    object_type: string;
    verbose_name: string;
    verbose_name_plural: string;

    static get(slug: string): Promise<Source> {
        return DefaultClient.fetch<Source>(["sources", "all", slug]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Source>> {
        return DefaultClient.fetch<AKResponse<Source>>(["sources", "all"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/sources/${rest}`;
    }
}
