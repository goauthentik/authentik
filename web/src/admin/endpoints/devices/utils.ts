import { FamilyEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

export function osFamilyToLabel(family: FamilyEnum | undefined): string {
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

export function getSize(size: number) {
    const sizes = [" Bytes", " KB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"];

    for (let i = 1; i < sizes.length; i++) {
        if (size < Math.pow(1024, i))
            return Math.round((size / Math.pow(1024, i - 1)) * 100) / 100 + sizes[i - 1];
    }
    return size.toString();
}
