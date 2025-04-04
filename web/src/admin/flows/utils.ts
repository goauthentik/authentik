import { msg } from "@lit/localize";

import { Flow, FlowDesignationEnum, FlowLayoutEnum } from "@goauthentik/api";

export function RenderFlowOption(flow: Flow): string {
    return `${flow.slug} (${flow.name})`;
}

export function DesignationToLabel(designation: FlowDesignationEnum): string {
    switch (designation) {
        case FlowDesignationEnum.Authentication:
            return msg("Authentication");
        case FlowDesignationEnum.Authorization:
            return msg("Authorization");
        case FlowDesignationEnum.Enrollment:
            return msg("Enrollment");
        case FlowDesignationEnum.Invalidation:
            return msg("Invalidation");
        case FlowDesignationEnum.Recovery:
            return msg("Recovery");
        case FlowDesignationEnum.StageConfiguration:
            return msg("Stage Configuration");
        case FlowDesignationEnum.Unenrollment:
            return msg("Unenrollment");
        case FlowDesignationEnum.UnknownDefaultOpenApi:
            return msg("Unknown designation");
    }
}

export function LayoutToLabel(layout: FlowLayoutEnum): string {
    switch (layout) {
        case FlowLayoutEnum.Stacked:
            return msg("Stacked");
        case FlowLayoutEnum.ContentLeft:
            return msg("Content left");
        case FlowLayoutEnum.ContentRight:
            return msg("Content right");
        case FlowLayoutEnum.SidebarLeft:
            return msg("Sidebar left");
        case FlowLayoutEnum.SidebarRight:
            return msg("Sidebar right");
        case FlowLayoutEnum.UnknownDefaultOpenApi:
            return msg("Unknown layout");
    }
}

/**
 * Applies the next URL as a query parameter to the given URL or URLSearchParams object.
 *
 * @todo deprecate this once hash routing is removed.
 */
export function applyNextParam(
    target: URL | URLSearchParams,
    destination: string | URL = window.location.pathname + "#" + window.location.hash,
): void {
    const searchParams = target instanceof URL ? target.searchParams : target;

    searchParams.set("next", destination.toString());
}

/**
 * Creates a URLSearchParams object with the next URL as a query parameter.
 *
 * @todo deprecate this once hash routing is removed.
 */
export function createNextSearchParams(
    destination: string | URL = window.location.pathname + "#" + window.location.hash,
): URLSearchParams {
    const searchParams = new URLSearchParams();

    applyNextParam(searchParams, destination);

    return searchParams;
}

/**
 * Creates a URL to a flow, with the next URL as a query parameter.
 *
 * @param flow The flow to create the URL for.
 * @param destination The next URL to redirect to after the flow is completed, `true` to use the current route.
 */
export function formatFlowURL(
    flow: Flow,
    destination: string | URL | null = window.location.pathname + "#" + window.location.hash,
): URL {
    const url = new URL(`/if/flow/${flow.slug}/`, window.location.origin);

    if (destination) {
        applyNextParam(url, destination);
    }

    return url;
}
