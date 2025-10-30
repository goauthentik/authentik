import type {
    LDAPProviderRequest,
    ModelRequest,
    OAuth2ProviderRequest,
    ProvidersSamlImportMetadataCreateRequest,
    ProxyProviderRequest,
    RACProviderRequest,
    RadiusProviderRequest,
    SAMLProviderRequest,
    SCIMProviderRequest,
} from "@goauthentik/api";
import { ProviderModelEnum } from "@goauthentik/api";

export type OneOfProvider = Partial<
    | SCIMProviderRequest
    | SAMLProviderRequest
    | ProvidersSamlImportMetadataCreateRequest
    | RACProviderRequest
    | RadiusProviderRequest
    | ProxyProviderRequest
    | OAuth2ProviderRequest
    | LDAPProviderRequest
>;

export type StrictProviderModelEnum = Exclude<
    ProviderModelEnum,
    typeof ProviderModelEnum.UnknownDefaultOpenApi
>;

/**
 * An extracted suffix of the provider model from the full provider model string.
 */
export type ProviderModelSuffix = ModelRequest["providerModel"] extends `${string}.${infer R}`
    ? R
    : never;

export function pluckProviderSuffix(value: ModelRequest["providerModel"]): ProviderModelSuffix {
    const suffix = value.split(".")[1] as ProviderModelSuffix;

    return suffix;
}

export const ProviderModelSuffixRecord = Object.fromEntries(
    Object.values(ProviderModelEnum)
        .filter(
            (providerEnumValue) => providerEnumValue !== ProviderModelEnum.UnknownDefaultOpenApi,
        )
        .map((value) => {
            const suffix = pluckProviderSuffix(value);

            return [suffix, value as StrictProviderModelEnum];
        }),
);
