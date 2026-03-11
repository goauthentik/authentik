import { Flow, FlowDesignationEnum, FlowLayoutEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

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
        case FlowLayoutEnum.SidebarLeftFrameBackground:
            return msg("Sidebar left (frame background)");
        case FlowLayoutEnum.SidebarRightFrameBackground:
            return msg("Sidebar right (frame background)");
        case FlowLayoutEnum.UnknownDefaultOpenApi:
            return msg("Unknown layout");
    }
}
