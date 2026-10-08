import { aki } from "#common/api/client";

import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { LitFC } from "#elements/types";

import {
    AKSearchSelect,
    AKSearchSelectField,
    SearchSelectFieldProps,
    SearchSelectProps,
} from "#components/ak-search-select-field";

import { RenderFlowOption } from "#admin/flows/utils";

import { Flow, FlowDesignationEnum, FlowsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";

export interface FlowSourceInit {
    /**
     * Only offer flows with this designation.
     */
    flowType?: FlowDesignationEnum;
    /**
     * Choose the flow with this slug when the field has no value.
     */
    defaultFlowSlug?: string | null;
}

const flowSources = new Map<string, SearchSelectSource<Flow>>();

/**
 * A search select source for flows.
 *
 * @remarks
 *   Sources are cached by their options, so rendering a field again passes the same source and
 *   doesn't refetch.
 */
export function flowSource({
    flowType,
    defaultFlowSlug,
}: FlowSourceInit = {}): SearchSelectSource<Flow> {
    const cacheKey = `${flowType ?? ""}:${defaultFlowSlug ?? ""}`;
    const cached = flowSources.get(cacheKey);

    if (cached) return cached;

    const source: SearchSelectSource<Flow> = {
        fetchObjects: (query) =>
            aki(FlowsApi)
                .flowsInstancesList(withQuery(query, { ordering: "slug", designation: flowType }))
                .then(({ results }) => results),
        keyOf: (flow) => flow.pk,
        labelOf: RenderFlowOption,
        describe: (flow) => flow.slug,
        preselect: defaultFlowSlug
            ? (flows) => flows.find((flow) => flow.slug === defaultFlowSlug)
            : undefined,
    };

    flowSources.set(cacheKey, source);

    return source;
}

export type FlowSearchProps = Omit<SearchSelectProps<Flow>, "source"> & FlowSourceInit;

function splitFlowProps<P extends FlowSearchProps>({ flowType, defaultFlowSlug, ...props }: P) {
    return { source: flowSource({ flowType, defaultFlowSlug }), props };
}

/**
 * A search select for choosing a flow.
 */
export const AKFlowSearch: LitFC<FlowSearchProps> = (flowProps) => {
    const { source, props } = splitFlowProps(flowProps);

    return AKSearchSelect({ placeholder: msg("Select a flow..."), ...props, source });
};

export type FlowFieldProps = Omit<SearchSelectFieldProps<Flow>, "source"> & FlowSourceInit;

/**
 * A complete form field for choosing a flow: its label, the search select, and help text.
 */
export const AKFlowField: LitFC<FlowFieldProps> = (flowProps) => {
    const { source, props } = splitFlowProps(flowProps);

    return AKSearchSelectField({ placeholder: msg("Select a flow..."), ...props, source });
};
