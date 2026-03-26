import { OutpostTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

export const embeddedOutpostManaged = "goauthentik.io/outposts/embedded";

export function outpostTypeToLabel(type?: OutpostTypeEnum): string {
    if (!type) return "";
    switch (type) {
        case OutpostTypeEnum.Proxy:
            return msg("Proxy");
        case OutpostTypeEnum.Ldap:
            return msg("LDAP");
        case OutpostTypeEnum.Radius:
            return msg("Radius");
        case OutpostTypeEnum.Rac:
            return msg("RAC");
        case OutpostTypeEnum.UnknownDefaultOpenApi:
            return msg("Unknown type");
    }
}
