import { Flow, FlowDesignationEnum, FlowLayoutEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

export function RenderFlowOption(flow: Flow): string {
    return `${flow.slug} (${flow.name})`;
}

const designationToLabel = {
    [FlowDesignationEnum.Authentication]: msg("Authentication"),
    [FlowDesignationEnum.UserSelection]: msg("User selection"),
    [FlowDesignationEnum.Authorization]: msg("Authorization"),
    [FlowDesignationEnum.Enrollment]: msg("Enrollment"),
    [FlowDesignationEnum.Invalidation]: msg("Invalidation"),
    [FlowDesignationEnum.Recovery]: msg("Recovery"),
    [FlowDesignationEnum.StageConfiguration]: msg("Stage Configuration"),
    [FlowDesignationEnum.Unenrollment]: msg("Unenrollment"),
    [FlowDesignationEnum.UnknownDefaultOpenApi]: msg("Unknown designation"),
};

export function DesignationToLabel(designation: FlowDesignationEnum): string {
    return (
        designationToLabel[designation] ??
        designationToLabel[FlowDesignationEnum.UnknownDefaultOpenApi]
    );
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
