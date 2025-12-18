import "#admin/common/ak-license-notice";

import type { TypeCreate } from "@goauthentik/api";

export type LocalTypeCreate = TypeCreate;

const providerPriority = [
    "oauth2provider",
    "samlprovider",
    "samlproviderimportmodel",
    "racprovider",
    "proxyprovider",
    "radiusprovider",
    "ldapprovider",
    "scimprovider",
];

export const providerTypePriority: Record<string, number> = providerPriority.reduce(
    (acc, name, index) => ({ ...acc, [name]: 95 - index * 5 }),
    {} satisfies Record<string, number>,
);
