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

export function trySortNumerical<T extends { id: string | number }>(a: T, b: T): number {
    let idA: string | number = a.id;
    let idB: string | number = b.id;
    try {
        if (typeof a.id === "string" && typeof b.id === "string") {
            idA = parseInt(a.id, 10);
            idB = parseInt(b.id, 10);
            return idA - idB;
        }
        if (typeof a.id === "number" && typeof b.id === "number") {
            return a.id - b.id;
        }
    } catch {
        //
    }
    return a.id.toString().localeCompare(b.id.toString());
}
