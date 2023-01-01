import { t } from "@lingui/macro";

import { UserMatchingModeEnum } from "@goauthentik/api";

export function UserMatchingModeToLabel(mode?: UserMatchingModeEnum): string {
    if (!mode) return "";
    switch (mode) {
        case UserMatchingModeEnum.Identifier:
            return t`Link users on unique identifier`;
        case UserMatchingModeEnum.EmailLink:
            return t`Link to a user with identical email address. Can have security implications when a source doesn't validate email addresses`;
        case UserMatchingModeEnum.EmailDeny:
            return t`Use the user's email address, but deny enrollment when the email address already exists`;
        case UserMatchingModeEnum.UsernameLink:
            return t`Link to a user with identical username. Can have security implications when a username is used with another source`;
        case UserMatchingModeEnum.UsernameDeny:
            return t`Use the user's username, but deny enrollment when the username already exists`;
        case UserMatchingModeEnum.UnknownDefaultOpenApi:
            return t`Unknown user matching mode`;
    }
}
