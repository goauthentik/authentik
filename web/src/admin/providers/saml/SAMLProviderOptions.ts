import { msg } from "@lit/localize";

import { DigestAlgorithmEnum, SignatureAlgorithmEnum, SpBindingEnum } from "@goauthentik/api";

type Option<T> = [string, T, boolean?];

function toOptions<T>(options: Option<T>[]) {
    return options.map(([label, value, isDefault]: Option<T>) => ({
        label,
        value,
        default: isDefault ?? false,
    }));
}

export const spBindingOptions = toOptions([
    [msg("Redirect"), SpBindingEnum.Redirect, true],
    [msg("Post"), SpBindingEnum.Post],
]);

export const digestAlgorithmOptions = toOptions([
    ["SHA1", DigestAlgorithmEnum.HttpWwwW3Org200009Xmldsigsha1],
    ["SHA256", DigestAlgorithmEnum.HttpWwwW3Org200104Xmlencsha256, true],
    ["SHA384", DigestAlgorithmEnum.HttpWwwW3Org200104XmldsigMoresha384],
    ["SHA512", DigestAlgorithmEnum.HttpWwwW3Org200104Xmlencsha512],
]);

export const signatureAlgorithmOptions = toOptions([
    ["RSA-SHA1", SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigrsaSha1],
    ["RSA-SHA256", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha256, true],
    ["RSA-SHA384", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha384],
    ["RSA-SHA512", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha512],
    ["ECDSA-SHA1", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha1],
    ["ECDSA-SHA256", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha256],
    ["ECDSA-SHA384", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha384],
    ["ECDSA-SHA512", SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMoreecdsaSha512],
    ["DSA-SHA1", SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigdsaSha1],
]);
