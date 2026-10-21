import { SidebarItemProperties } from "#elements/sidebar/SidebarItem";
import { LitPropertyRecord } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";
import { repeat } from "lit/directives/repeat.js";

export type SidebarAttributes =
    | LitPropertyRecord<SidebarItemProperties & { enterprise?: boolean }>
    | string[]
    | null;

// A `string[]` in the attributes slot lists the route names that keep the entry active.
export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: SidebarAttributes,
    children?: SidebarEntry[],
];

export type RouteNameResolver = (path: string) => string | null;

/**
 * Recursively renders a collection of sidebar entries.
 */
export function renderSidebarItems(
    entries: readonly SidebarEntry[],
    resolveRouteName: RouteNameResolver,
) {
    return repeat(
        entries,
        ([path, label]) => path || label,
        // eslint-disable-next-line @typescript-eslint/no-use-before-define
        (entry) => renderSidebarItem(entry, resolveRouteName),
    );
}

/**
 * Recursively renders a sidebar entry.
 */
export function renderSidebarItem(
    [path, label, attributes, children]: SidebarEntry,
    resolveRouteName: RouteNameResolver,
): TemplateResult {
    const properties = Array.isArray(attributes)
        ? {
              ".activeWhen": (activePath: string) =>
                  attributes.includes(resolveRouteName(activePath) ?? ""),
          }
        : (attributes ?? {});

    if (path) {
        properties.path = path;
    }

    return html`<ak-sidebar-item
        exportparts="list-item, link"
        label=${ifDefined(label)}
        ${spread(properties)}
    >
        ${children ? renderSidebarItems(children, resolveRouteName) : null}
    </ak-sidebar-item>`;
}

/**
 * The label of the entry that lists the given route, e.g. "Providers" for `provider-view`.
 */
export function findSidebarSectionByRoute(
    entries: readonly SidebarEntry[],
    routeName: string | null,
): string | null {
    if (!routeName) return null;

    for (const [, label, attributes, children] of entries) {
        if (Array.isArray(attributes) && attributes.includes(routeName)) return label;

        const childLabel = children ? findSidebarSectionByRoute(children, routeName) : null;

        if (childLabel) return childLabel;
    }

    return null;
}
