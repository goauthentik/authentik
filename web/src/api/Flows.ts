import { DefaultClient, PBResponse, QueryArguments } from "./Client";

export enum FlowDesignation {
    Authentication = "authentication",
    Authorization = "authorization",
    Invalidation = "invalidation",
    Enrollment = "enrollment",
    Unrenollment = "unenrollment",
    Recovery = "recovery",
    StageConfiguration = "stage_configuration",
}

export class Flow {
    pk: string;
    policybindingmodel_ptr_id: string;
    name: string;
    slug: string;
    title: string;
    designation: FlowDesignation;
    background: string;
    stages: string[];
    policies: string[];
    cache_count: number;

    constructor() {
        throw Error();
    }

    static get(slug: string): Promise<Flow> {
        return DefaultClient.fetch<Flow>(["flows", "instances", slug]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Flow>> {
        return DefaultClient.fetch<PBResponse<Flow>>(["flows", "instances"], filter);
    }

    static cached(): Promise<number> {
        return DefaultClient.fetch<PBResponse<Flow>>(["flows", "cached"]).then(r => {
            return r.pagination.count;
        });
    }
}

export class Stage {
    pk: string;
    name: string;
    __type__: string;
    verbose_name: string;

    constructor() {
        throw Error();
    }
}

export class FlowStageBinding {

    pk: string;
    policybindingmodel_ptr_id: string;
    target: string;
    stage: string;
    stage_obj: Stage;
    evaluate_on_plan: boolean;
    re_evaluate_policies: boolean;
    order: number;
    policies: string[];

    constructor() {
        throw Error();
    }

    static get(slug: string): Promise<FlowStageBinding> {
        return DefaultClient.fetch<FlowStageBinding>(["flows", "bindings", slug]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<FlowStageBinding>> {
        return DefaultClient.fetch<PBResponse<FlowStageBinding>>(["flows", "bindings"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/stages/bindings/${rest}`;
    }
}
