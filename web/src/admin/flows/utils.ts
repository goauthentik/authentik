import { msg } from "@lit/localize";

import { Flow, FlowDesignationEnum, LayoutEnum } from "@goauthentik/api";

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

export function LayoutToLabel(layout: LayoutEnum): string {
    switch (layout) {
        case LayoutEnum.Stacked:
            return msg("Stacked");
        case LayoutEnum.ContentLeft:
            return msg("Content left");
        case LayoutEnum.ContentRight:
            return msg("Content right");
        case LayoutEnum.SidebarLeft:
            return msg("Sidebar left");
        case LayoutEnum.SidebarRight:
            return msg("Sidebar right");
        case LayoutEnum.UnknownDefaultOpenApi:
            return msg("Unknown layout");
    }
}
