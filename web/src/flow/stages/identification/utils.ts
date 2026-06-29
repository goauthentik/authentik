import { LoginSource, UserFieldsEnum } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";

export const OR_LIST_FORMATTERS: Intl.ListFormat = new Intl.ListFormat("default", {
    style: "short",
    type: "disjunction",
});

export const UIFieldLabels: Record<UserFieldsEnum, () => string> = {
    [UserFieldsEnum.Username]: () => msg("Username"),
    [UserFieldsEnum.Email]: () => msg("Email"),
    [UserFieldsEnum.Upn]: () => msg("UPN"),
    [UserFieldsEnum.UnknownDefaultOpenApi]: () => msg("Unknown Field"),
};

/**
 * Given a UserFieldsEnum or string, returns a human-readable label for the field.
 */
export function formatUIFieldLabel(fieldLike: UserFieldsEnum | string): string {
    if (Object.hasOwn(UIFieldLabels, fieldLike)) {
        return UIFieldLabels[fieldLike as UserFieldsEnum]();
    }

    return msg(str`Unknown Field ${fieldLike}`);
}

export function compareLoginSource(a: LoginSource, b: LoginSource) {
    return match([!!a.promoted, !!b.promoted])
        .with([true, false], () => -1)
        .with([false, true], () => 1)
        .otherwise(() => 0);
}
