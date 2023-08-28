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
    ["SHA1", DigestAlgorithmEnum._200009Xmldsigsha1],
    ["SHA256", DigestAlgorithmEnum._200104Xmlencsha256, true],
    ["SHA384", DigestAlgorithmEnum._200104XmldsigMoresha384],
    ["SHA512", DigestAlgorithmEnum._200104Xmlencsha512],
]);

export const signatureAlgorithmOptions = toOptions([
    ["RSA-SHA1", SignatureAlgorithmEnum._200009XmldsigrsaSha1],
    ["RSA-SHA256", SignatureAlgorithmEnum._200104XmldsigMorersaSha256, true],
    ["RSA-SHA384", SignatureAlgorithmEnum._200104XmldsigMorersaSha384],
    ["RSA-SHA512", SignatureAlgorithmEnum._200104XmldsigMorersaSha512],
    ["DSA-SHA1", SignatureAlgorithmEnum._200009XmldsigdsaSha1],
]);
