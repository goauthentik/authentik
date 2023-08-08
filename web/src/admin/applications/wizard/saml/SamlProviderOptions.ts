import { msg } from "@lit/localize";

import { DigestAlgorithmEnum, SignatureAlgorithmEnum, SpBindingEnum } from "@goauthentik/api";

export const spBindingOptions = [
    {
        label: msg("Redirect"),
        value: SpBindingEnum.Redirect,
        default: true,
    },
    {
        label: msg("Post"),
        value: SpBindingEnum.Post,
    },
];

export const digestAlgorithmOptions = [
    {
        label: "SHA1",
        value: DigestAlgorithmEnum._200009Xmldsigsha1,
    },
    {
        label: "SHA256",
        value: DigestAlgorithmEnum._200104Xmlencsha256,
        default: true,
    },
    {
        label: "SHA384",
        value: DigestAlgorithmEnum._200104XmldsigMoresha384,
    },
    {
        label: "SHA512",
        value: DigestAlgorithmEnum._200104Xmlencsha512,
    },
];

export const signatureAlgorithmOptions = [
    {
        label: "RSA-SHA1",
        value: SignatureAlgorithmEnum._200009XmldsigrsaSha1,
    },
    {
        label: "RSA-SHA256",
        value: SignatureAlgorithmEnum._200104XmldsigMorersaSha256,
        default: true,
    },
    {
        label: "RSA-SHA384",
        value: SignatureAlgorithmEnum._200104XmldsigMorersaSha384,
    },
    {
        label: "RSA-SHA512",
        value: SignatureAlgorithmEnum._200104XmldsigMorersaSha512,
    },
    {
        label: "DSA-SHA1",
        value: SignatureAlgorithmEnum._200009XmldsigdsaSha1,
    },
];
