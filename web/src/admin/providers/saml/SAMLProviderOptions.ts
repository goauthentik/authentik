import { openAPIEnumOptions } from "#common/api/enums";

import {
    DigestAlgorithmEnum,
    KeyTypeEnum,
    SAMLBindingsEnum,
    SAMLLogoutMethods,
    SignatureAlgorithmEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";

type Option<T> = [string, T, boolean?];

function toOptions<T>(options: Option<T>[]) {
    return options.map(([label, value, isDefault]: Option<T>) => ({
        label,
        value,
        default: isDefault ?? false,
    }));
}

export const spBindingOptions = toOptions([
    [msg("Redirect"), SAMLBindingsEnum.Redirect, true],
    [msg("Post"), SAMLBindingsEnum.Post],
]);

export function logoutMethodLabel(method?: SAMLLogoutMethods | string): string {
    switch (method) {
        case SAMLLogoutMethods.FrontchannelIframe:
            return msg("Front-channel (Iframe)");
        case SAMLLogoutMethods.FrontchannelNative:
            return msg("Front-channel (Native)");
        case SAMLLogoutMethods.Backchannel:
            return msg("Back-channel (POST)");
        default:
            return method ?? "";
    }
}

export function logoutMethodOptions(hasPostBinding: boolean) {
    return [
        {
            label: logoutMethodLabel(SAMLLogoutMethods.FrontchannelIframe),
            value: SAMLLogoutMethods.FrontchannelIframe,
            default: true,
        },
        {
            label: logoutMethodLabel(SAMLLogoutMethods.FrontchannelNative),
            value: SAMLLogoutMethods.FrontchannelNative,
        },
        {
            label: logoutMethodLabel(SAMLLogoutMethods.Backchannel),
            value: SAMLLogoutMethods.Backchannel,
            disabled: !hasPostBinding,
        },
    ];
}

export const digestAlgorithmOptions = openAPIEnumOptions(DigestAlgorithmEnum).map((option) => ({
    ...option,
    default: option.value === DigestAlgorithmEnum.SHA256,
}));

export const signatureAlgorithmOptions = openAPIEnumOptions(SignatureAlgorithmEnum).map(
    (option) => ({
        ...option,
        default: option.value === SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha256,
    }),
);

const SAML_SOURCE_SIGNATURE_ALGORITHMS: readonly SignatureAlgorithmEnum[] = [
    SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigrsaSha1,
    SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha256,
    SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha384,
    SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha512,
    SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigdsaSha1,
];

export const samlSourceSignatureAlgorithmOptions = signatureAlgorithmOptions.filter((option) =>
    SAML_SOURCE_SIGNATURE_ALGORITHMS.includes(option.value),
);

export type HashAlgorithm = "SHA1" | "SHA256" | "SHA384" | "SHA512";

export const DEFAULT_HASH_ALGORITHM: HashAlgorithm = "SHA256";

export const availableHashes: HashAlgorithm[] = ["SHA1", "SHA256", "SHA384", "SHA512"];

export const SignatureFamilyByHashAlgorithm: Partial<
    Record<KeyTypeEnum, ReadonlyMap<HashAlgorithm, SignatureAlgorithmEnum>>
> = {
    [KeyTypeEnum.RSA]: new Map([
        ["SHA1", SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigrsaSha1],
        ["SHA256", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha256],
        ["SHA384", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha384],
        ["SHA512", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha512],
    ]),
    [KeyTypeEnum.EC]: new Map([
        ["SHA1", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha1],
        ["SHA256", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha256],
        ["SHA384", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha384],
        ["SHA512", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha512],
    ]),
    [KeyTypeEnum.DSA]: new Map([["SHA1", SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigdsaSha1]]),
};

export function retrieveSignatureAlgorithm(
    family: KeyTypeEnum,
    algorithm: HashAlgorithm,
): SignatureAlgorithmEnum | null {
    const familyMap = SignatureFamilyByHashAlgorithm[family];
    if (!familyMap) return null;

    return familyMap.get(algorithm) ?? null;
}

export const SAMLSupportedKeyTypes = [KeyTypeEnum.RSA, KeyTypeEnum.EC, KeyTypeEnum.DSA];
