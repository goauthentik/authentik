import { MessageFormatter } from "#common/ui/locale/format";

import { CheckboxItem } from "#elements/ak-checkbox-group/ak-checkbox-group";

import { GrantTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

export const GrantTypeLabelRecord: Record<GrantTypeEnum, MessageFormatter<string>> = {
    [GrantTypeEnum.AuthorizationCode]: () => msg("Authorization Code"),
    [GrantTypeEnum.Implicit]: () => msg("Implicit"),
    [GrantTypeEnum.Hybrid]: () => msg("Hybrid"),
    [GrantTypeEnum.RefreshToken]: () => msg("Refresh token"),
    [GrantTypeEnum.ClientCredentials]: () => msg("Client credentials"),
    [GrantTypeEnum.Password]: () => msg("Password"),
    [GrantTypeEnum.UrnIetfParamsOauthGrantTypeDeviceCode]: () => msg("Device-code"),
    [GrantTypeEnum.UrnIetfParamsOauthGrantTypeTokenExchange]: () => msg("Token exchange"),
    [GrantTypeEnum.UnknownDefaultOpenApi]: () => msg("Unknown Grant type"),
};

export const GrantTypeCheckboxItems: CheckboxItem<GrantTypeEnum>[] = [
    GrantTypeEnum.AuthorizationCode,
    GrantTypeEnum.Implicit,
    GrantTypeEnum.Hybrid,
    GrantTypeEnum.RefreshToken,
    GrantTypeEnum.ClientCredentials,
    GrantTypeEnum.Password,
    GrantTypeEnum.UrnIetfParamsOauthGrantTypeDeviceCode,
    GrantTypeEnum.UrnIetfParamsOauthGrantTypeTokenExchange,
].map((grantType) => ({
    name: grantType,
    label: GrantTypeLabelRecord[grantType](),
}));
