import { StorageAccessor } from "#common/storage";
import type { LayoutType } from "#common/ui/config";

import type { Application } from "@goauthentik/api";

export type AppGroupEntry = [label: string, applications: Application[]];

export type PageUIConfig = {
    layout: LayoutType;
    background?: string;
    searchEnabled: boolean;
};

export enum ViewMode {
    Grid = "grid",
    List = "list",
}

export const VIEW_MODE_STORAGE = StorageAccessor.local("ak-library-view-mode");
