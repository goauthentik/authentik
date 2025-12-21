import type { LayoutType } from "#common/ui/config";

import type { Application } from "@goauthentik/api";

export type AppGroupEntry = [label: string, applications: Application[]];

export type PageUIConfig = {
    layout: LayoutType;
    background?: string;
    searchEnabled: boolean;
};
