import { t } from "@lingui/macro";

import { FlowDesignationEnum, LayoutEnum } from "@goauthentik/api";

export function DesignationToLabel(designation: FlowDesignationEnum): string {
    switch (designation) {
        case FlowDesignationEnum.Authentication:
            return t`Authentication`;
        case FlowDesignationEnum.Authorization:
            return t`Authorization`;
        case FlowDesignationEnum.Enrollment:
            return t`Enrollment`;
        case FlowDesignationEnum.Invalidation:
            return t`Invalidation`;
        case FlowDesignationEnum.Recovery:
            return t`Recovery`;
        case FlowDesignationEnum.StageConfiguration:
            return t`Stage Configuration`;
        case FlowDesignationEnum.Unenrollment:
            return t`Unenrollment`;
    }
}

export function LayoutToLabel(layout: LayoutEnum): string {
    switch (layout) {
        case LayoutEnum.Stacked:
            return t`Stacked`;
        case LayoutEnum.ContentLeft:
            return t`Content left`;
        case LayoutEnum.ContentRight:
            return t`Content right`;
        case LayoutEnum.SidebarLeft:
            return t`Sidebar left`;
        case LayoutEnum.SidebarRight:
            return t`Sidebar right`;
    }
}
