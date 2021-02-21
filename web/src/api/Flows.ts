import { DefaultClient, AKResponse, QueryArguments, BaseInheritanceModel } from "./Client";
import { TypeCreate } from "./Providers";

export enum ChallengeTypes {
    native = "native",
    response = "response",
    shell = "shell",
    redirect = "redirect",
}

export interface Error {
    code: string;
    string: string;
}

export interface ErrorDict {
    [key: string]: Error[];
}

export interface Challenge {
    type: ChallengeTypes;
    component?: string;
    title?: string;
    response_errors?: ErrorDict;
}
export interface WithUserInfoChallenge extends Challenge {
    pending_user: string;
    pending_user_avatar: string;
}

export interface ShellChallenge extends Challenge {
    body: string;
}
export interface RedirectChallenge extends Challenge {
    to: string;
}

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

    static diagram(slug: string): Promise<{ diagram: string }> {
        return DefaultClient.fetch<{ diagram: string }>(["flows", "instances", slug, "diagram"]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Flow>> {
        return DefaultClient.fetch<AKResponse<Flow>>(["flows", "instances"], filter);
    }

    static cached(): Promise<number> {
        return DefaultClient.fetch<{ count: number }>(["flows", "instances", "cached"]).then(r => {
            return r.count;
        });
    }

    static executor(slug: string): Promise<Challenge> {
        return DefaultClient.fetch(["flows", "executor", slug]);
    }

    static adminUrl(rest: string): string {
        return `/administration/flows/${rest}`;
    }
}

export class Stage implements BaseInheritanceModel {
    pk: string;
    name: string;
    object_type: string;
    verbose_name: string;
    verbose_name_plural: string;
    flow_set: Flow[];

    constructor() {
        throw Error();
    }

    static get(slug: string): Promise<Stage> {
        return DefaultClient.fetch<Stage>(["stages", "all", slug]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<Stage>> {
        return DefaultClient.fetch<AKResponse<Stage>>(["stages", "all"], filter);
    }

    static getTypes(): Promise<TypeCreate[]> {
        return DefaultClient.fetch<TypeCreate[]>(["stages", "all", "types"]);
    }

    static adminUrl(rest: string): string {
        return `/administration/stages/${rest}`;
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

    static list(filter?: QueryArguments): Promise<AKResponse<FlowStageBinding>> {
        return DefaultClient.fetch<AKResponse<FlowStageBinding>>(["flows", "bindings"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/stages/bindings/${rest}`;
    }
}
