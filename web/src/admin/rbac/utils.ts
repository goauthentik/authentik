import { msg } from "@lit/localize";

import { InitialPermissionsModeEnum } from "@goauthentik/api";

export function InitialPermissionsModeToLabel(mode: InitialPermissionsModeEnum): string {
    switch (mode) {
        case InitialPermissionsModeEnum.User:
            return msg("User");
        case InitialPermissionsModeEnum.Role:
            return msg("Role");
        case InitialPermissionsModeEnum.UnknownDefaultOpenApi:
            return msg("Unknown Initial Permissions mode");
    }
}
