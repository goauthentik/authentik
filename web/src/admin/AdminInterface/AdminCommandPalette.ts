import { navigate } from "#elements/router/RouterOutlet";

import { msg } from "@lit/localize";

import type { SidebarEntry } from "./AdminSidebar.js";

export interface CommandPaletteAction {
    id: string;
    title: string;
    section?: string;
    icon?: string;
    handler: () => void;
}

export interface BuildAdminCommandPaletteActionsOptions {
    sidebarEntries: readonly SidebarEntry[];
    enterpriseSidebarEntries?: readonly SidebarEntry[];
    includeEnterprise: boolean;
}

interface FlattenedSidebarCommand {
    path: string;
    label: string;
    section?: string;
    icon?: string;
    enterpriseOnly: boolean;
}

function isEnterpriseOnly(attributes: SidebarEntry[2]): boolean {
    if (!attributes || Array.isArray(attributes)) {
        return false;
    }

    return attributes.enterprise === true;
}

function paletteIcon(faClass: string): string {
    return `<i class="fas ${faClass}" aria-hidden="true"></i>`;
}

function flattenSidebarEntries(
    entries: readonly SidebarEntry[],
    currentSection?: string,
    currentIcon?: string,
): FlattenedSidebarCommand[] {
    const commands: FlattenedSidebarCommand[] = [];

    for (const entry of entries) {
        const [path, label, attributes, children, icon] = entry;

        // Section entries (no path) pass their icon down to children
        const inheritedIcon = icon ?? currentIcon;

        if (path) {
            commands.push({
                path,
                label,
                section: currentSection,
                icon: inheritedIcon ? paletteIcon(inheritedIcon) : undefined,
                enterpriseOnly: isEnterpriseOnly(attributes),
            });
        }

        if (children) {
            const childSection = path ? currentSection : label;
            commands.push(...flattenSidebarEntries(children, childSection, inheritedIcon));
        }
    }

    return commands;
}

export function buildAdminCommandPaletteActions({
    sidebarEntries,
    enterpriseSidebarEntries = [],
    includeEnterprise,
}: BuildAdminCommandPaletteActionsOptions): CommandPaletteAction[] {
    const commands = flattenSidebarEntries([...sidebarEntries, ...enterpriseSidebarEntries]);
    const seenPaths = new Set<string>();

    const actions = commands
        .filter((command) => {
            if (command.enterpriseOnly && !includeEnterprise) {
                return false;
            }

            if (seenPaths.has(command.path)) {
                return false;
            }

            seenPaths.add(command.path);
            return true;
        })
        .map<CommandPaletteAction>((command) => ({
            id: `admin:${command.path}`,
            title: command.label,
            section: command.section,
            icon: command.icon,
            handler: () => navigate(command.path),
        }));

    actions.push({
        id: "admin:go-to-user-interface",
        title: msg("Go to my User page"),
        section: msg("Navigation"),
        icon: paletteIcon("fa-compass"),
        handler: () => window.location.assign("/if/user/"),
    });

    return actions;
}
