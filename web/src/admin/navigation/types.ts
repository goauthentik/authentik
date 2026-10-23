import { type SidebarItem } from "#elements/sidebar/types";
import { type LitPropertyRecord } from "#elements/types";

export interface SidebarEntryProperties {
    key?: string;
    enterprise?: boolean;
}

export type SidebarAttributeObject = LitPropertyRecord<
    SidebarEntryProperties & { "?expanded": boolean }
>;

export type ExtendedSidebarItem = SidebarItem & {
    children?: ExtendedSidebarItem[];
    enterprise: boolean;
    route?: string;
};

export type SidebarAttributes = SidebarAttributeObject | string[] | null;

export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: SidebarAttributes,
    children?: SidebarEntry[],
];

export type SidebarLicenseFlags = { licensed: boolean; canEnterprise: boolean };

export const isSidebarAttributeObject = (a: unknown): a is SidebarAttributeObject =>
    a !== null && !Array.isArray(a) && typeof a === "object";

export const isEnterpriseEntry = (attr: SidebarAttributes | undefined) =>
    attr !== null && !Array.isArray(attr) && typeof attr === "object" && attr.enterprise;
