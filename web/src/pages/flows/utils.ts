import { t } from "@lingui/macro";

import { FlowDesignationEnum } from "@goauthentik/api";

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
