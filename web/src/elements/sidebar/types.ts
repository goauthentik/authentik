import { TemplateResult } from "lit";

// Does *not* have to ape the SidebarEntry in Admin.

export interface SidebarItem {
    label: string;
    key: string;
    path?: string | null;
    notice?: string | TemplateResult | null;
    children?: SidebarItem[];
}
