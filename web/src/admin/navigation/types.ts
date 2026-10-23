import { type SidebarItem } from "#elements/sidebar/types";

export interface SidebarEntryProperties {
    key?: string;
    enterprise?: boolean;
    expanded?: boolean;
}

export type ExtendedSidebarItem = SidebarItem & {
    children?: ExtendedSidebarItem[];
    enterprise: boolean;
    routes?: string[];
};

// A `string[]` in the attributes slot lists the route names that keep the entry active.
export type SidebarAttributes = SidebarEntryProperties | string[] | null;

export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: SidebarAttributes,
    children?: SidebarEntry[],
];

export type SidebarLicenseFlags = { licensed: boolean; canEnterprise: boolean };

export const isSidebarAttributeObject = (a: unknown): a is SidebarEntryProperties =>
    a !== null && !Array.isArray(a) && typeof a === "object";

export const isEnterpriseEntry = (attr: SidebarAttributes | undefined) =>
    attr !== null && !Array.isArray(attr) && typeof attr === "object" && attr.enterprise;
