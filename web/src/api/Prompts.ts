import { DefaultClient, QueryArguments, AKResponse } from "./Client";
import { Stage } from "./Flows";

export class Prompt {

    pk: string;
    field_key: string;
    label: string;
    type: string;
    required: boolean;
    placeholder: string;
    order: number;
    promptstage_set: Stage[];

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Prompt> {
        return DefaultClient.fetch<Prompt>(["stages", "prompt", "prompts", pk]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Prompt>> {
        return DefaultClient.fetch<AKResponse<Prompt>>(["stages", "prompt", "prompts"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/stages/prompts/${rest}`;
    }
}
