import { TemplateResult } from "lit";

// Does *not* have to ape the SidebarEntry in Admin.

export interface SidebarItem {
    label: string;
    key: string;
    icon?: string;
    expanded?: boolean;
    path?: string | null;
    notice?: string | TemplateResult | null;
    children?: SidebarItem[];
}

export type SidebarItemWithChildren = Omit<SidebarItem, "children"> &
    Required<Pick<SidebarItem, "children">>;

export type SidebarItemWithPath = Omit<SidebarItem, "path"> & Required<Pick<SidebarItem, "path">>;

export type SidebarItemWithBoth = Omit<SidebarItem, "path" | "children"> &
    Required<Pick<SidebarItem, "path" | "children">>;
