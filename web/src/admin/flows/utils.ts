import { msg } from "@lit/localize";

import { Flow, FlowDesignationEnum, LayoutEnum } from "@goauthentik/api";

export function RenderFlowOption(flow: Flow): string {
    return `${flow.slug} (${flow.name})`;
}

type FlowDesignationPair = [FlowDesignationEnum, string];

export const flowDesignationTable: FlowDesignationPair[] = [
    [FlowDesignationEnum.Authentication, msg("Authentication")],
    [FlowDesignationEnum.Authorization, msg("Authorization")],
    [FlowDesignationEnum.Enrollment, msg("Enrollment")],
    [FlowDesignationEnum.Invalidation, msg("Invalidation")],
    [FlowDesignationEnum.Recovery, msg("Recovery")],
    [FlowDesignationEnum.StageConfiguration, msg("Stage Configuration")],
    [FlowDesignationEnum.Unenrollment, msg("Unenrollment")],
];

// prettier-ignore
const flowDesignations = new Map(flowDesignationTable);

export function DesignationToLabel(designation: FlowDesignationEnum): string {
    return flowDesignations.get(designation) ?? msg("Unknown designation");
}

const layoutToLabel = new Map<LayoutEnum, string>([
    [LayoutEnum.Stacked, msg("Stacked")],
    [LayoutEnum.ContentLeft, msg("Content left")],
    [LayoutEnum.ContentRight, msg("Content right")],
    [LayoutEnum.SidebarLeft, msg("Sidebar left")],
    [LayoutEnum.SidebarRight, msg("Sidebar right")],
]);

export function LayoutToLabel(layout: LayoutEnum): string {
    return layoutToLabel.get(layout) ?? msg("Unknown layout");
}
