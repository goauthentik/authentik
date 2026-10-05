import type { SidebarItemProperties } from "#elements/sidebar/SidebarItem";
import type { LitPropertyRecord } from "#elements/types";

// The second attribute type is of string[] to help with the 'activeWhen' control, which was
// commonplace and singular enough to merit its own handler.

export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: LitPropertyRecord<SidebarItemProperties> | string[] | null,
    children?: SidebarEntry[],
];
