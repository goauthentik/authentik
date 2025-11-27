import { DeviceFactsOSFamily } from "@goauthentik/api";

import { msg } from "@lit/localize";

export function osFamilyToLabel(family: DeviceFactsOSFamily | undefined): string {
    switch (family) {
        case DeviceFactsOSFamily.Linux:
            return msg("Linux");
        case DeviceFactsOSFamily.Unix:
            return msg("Unix");
        case DeviceFactsOSFamily.Bsd:
            return msg("BSD");
        case DeviceFactsOSFamily.Windows:
            return msg("Windows");
        case DeviceFactsOSFamily.MacOs:
            return msg("macOS");
        case DeviceFactsOSFamily.Android:
            return msg("Android");
        case DeviceFactsOSFamily.IOs:
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
