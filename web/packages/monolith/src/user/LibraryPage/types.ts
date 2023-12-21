import type { LayoutType } from "@goauthentik/common/ui/config";

import type { Application } from "@goauthentik/api";

export type AppGroupEntry = [string, Application[]];
export type AppGroupList = AppGroupEntry[];

export type PageUIConfig = {
    layout: LayoutType;
    background?: string;
    searchEnabled: boolean;
};
