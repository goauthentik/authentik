import { TemplateResult } from "lit";

export type SidebarEventHandler = () => void;

export type SidebarAttributes = {
    isAbsoluteLink?: boolean | (() => boolean);
    highlight?: boolean | (() => boolean);
    expanded?: boolean | (() => boolean);
    activeWhen?: string[];
    isActive?: boolean;
};

export type SidebarEntry = {
    path: string | SidebarEventHandler | null;
    label: string;
    attributes?: SidebarAttributes | null; // eslint-disable-line
    children?: SidebarEntry[];
};

// Typescript requires the type here to correctly type the recursive path
export type SidebarRenderer = (_: SidebarEntry) => TemplateResult;
