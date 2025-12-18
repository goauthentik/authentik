import "#admin/common/ak-license-notice";

import type { TypeCreate } from "@goauthentik/api";

export type LocalTypeCreate = TypeCreate;

export const providerTypePriority: Record<string, number> = {
    oauth2provider: 95,
    samlprovider: 90,
    samlproviderimportmodel: 85,
    racprovider: 80,
    proxyprovider: 75,
    radiusprovider: 70,
    ldapprovider: 65,
    scimprovider: 60,
};
