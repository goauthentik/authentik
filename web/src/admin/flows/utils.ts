import { msg } from "@lit/localize";

import { Flow, FlowDesignationEnum, FlowLayoutEnum } from "@goauthentik/api";

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

const layoutToLabel = new Map<FlowLayoutEnum, string>([
    [FlowLayoutEnum.Stacked, msg("Stacked")],
    [FlowLayoutEnum.ContentLeft, msg("Content left")],
    [FlowLayoutEnum.ContentRight, msg("Content right")],
    [FlowLayoutEnum.SidebarLeft, msg("Sidebar left")],
    [FlowLayoutEnum.SidebarRight, msg("Sidebar right")],
]);

export function LayoutToLabel(layout: FlowLayoutEnum): string {
    return layoutToLabel.get(layout) ?? msg("Unknown layout");
}
