import { InitialPermissionsModeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

export function InitialPermissionsModeToLabel(mode: InitialPermissionsModeEnum): string {
    switch (mode) {
        case InitialPermissionsModeEnum.User:
            return msg("User", {
                id: "label.initial.permissions.user",
                desc: "Label for initial permissions user mode",
            });
        case InitialPermissionsModeEnum.Role:
            return msg("Role", {
                id: "label.initial.permissions.role",
                desc: "Label for initial permissions role mode",
            });
        case InitialPermissionsModeEnum.UnknownDefaultOpenApi:
            return msg("Unknown Initial Permissions mode");
    }
}
