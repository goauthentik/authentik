import { FamilyEnum } from "@goauthentik/api";
import { msg } from "@lit/localize";

export function osFamilyToLabel(family: FamilyEnum | undefined) : string {
    switch (family) {
        case FamilyEnum.Linux:
            return msg("Linux");
        case FamilyEnum.Unix:
            return msg("Unix");
        case FamilyEnum.Bsd:
            return msg("BSD");
        case FamilyEnum.Windows:
            return msg("Windows");
        case FamilyEnum.MacOs:
            return msg("macOS");
        case FamilyEnum.Android:
            return msg("Android");
        case FamilyEnum.IOs:
            return msg("iOS");
    }
    return msg("Unknown");
}
