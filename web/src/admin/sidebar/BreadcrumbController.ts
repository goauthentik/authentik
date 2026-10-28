import { ExtendedSidebarItem } from "./types";

import { toAdminInterface } from "#elements/router/core/interfaces";
import { currentInterfacePath } from "#elements/router/core/interfaces";
import { identifyingKeys } from "#elements/router/core/matcher";
import { matchRoute, RouteMatch, sameRouteMatch } from "#elements/router/core/matcher";
import { RouteLike } from "#elements/router/core/Route";
import { PageDetailsUpdate } from "#elements/router/meta";
import { SidebarItem } from "#elements/sidebar/types";
import { ActiveTabChangeEvent } from "#elements/tabs/tab-events";

import { type AdminInterface } from "#admin/ak-interface-admin";
import { ROUTES } from "#admin/Routes";
import { findSidebarEntries, matchesPath } from "#admin/sidebar/sidebarTools";

import { ContextProvider, createContext } from "@lit/context";
import { ReactiveController } from "lit";

export interface Crumb {
    path: string | null;
    label: string;
}

export interface BreadcrumbEntries {
    path: string;
    objectPath: string | null;
    crumbs: Crumb[];
    fullCrumbs: Crumb[];
}

export interface BreadcrumbEntriesInit {
    pathname: string;
    path: string;
    match: RouteMatch<RouteLike>;
    objectName: string | null;
    tabLabel: string | null;
}

export const BreadcrumbContext = createContext<BreadcrumbEntries | null>(
    Symbol("authentik-breadcrumb-context"),
);

const sameEntries = (a: BreadcrumbEntries | null, b: BreadcrumbEntries) =>
    !!a &&
    a.path === b.path &&
    a.objectPath === b.objectPath &&
    a.crumbs.length === b.crumbs.length &&
    JSON.stringify(a.fullCrumbs) === JSON.stringify(b.fullCrumbs);

export function findBreadcrumbEntries(
    entries: readonly ExtendedSidebarItem[],
    { pathname, path, match, objectName, tabLabel }: BreadcrumbEntriesInit,
): BreadcrumbEntries {
    const sweepCrumbs = ({ label, path }: SidebarItem) => ({ label, path: path ?? null });

    const sections = findSidebarEntries(entries, matchesPath(path, match?.route.name ?? null)).map(
        sweepCrumbs,
    );

    // Yeah, it's a string. Javascripts "arrays are just objects with funny keys" thing sucks.
    const tail = match?.parameters["0"] || null;

    const objectPath =
        !!match && identifyingKeys(match.parameters).length > 0
            ? toAdminInterface(tail ? path.slice(0, -1 * (tail.length + 1)) : path)
            : null;

    const crumbs =
        objectPath && objectName
            ? [...sections, { label: objectName, path: objectPath }]
            : sections;

    const fullCrumbs = tail && tabLabel ? [...crumbs, { label: tabLabel, path: null }] : crumbs;

    return { path: pathname, objectPath, crumbs, fullCrumbs };
}

export class BreadcrumbController implements ReactiveController {
    protected provider: ContextProvider<typeof BreadcrumbContext>;

    #pathname: string | null = null;
    #match: RouteMatch<RouteLike> | null = null;
    #objectName: string | null = null;
    #tabLabel: string | null = null;

    #abortController: AbortController | null = null;

    constructor(protected host: AdminInterface) {
        this.provider = new ContextProvider(this.host, {
            context: BreadcrumbContext,
            initialValue: null,
        });

        host.addController(this);
    }

    protected pageDetailsListener = (event: PageDetailsUpdate) => {
        this.#objectName = event.header.header ?? null;
        this.publish();
    };

    protected activeTabListener = (event: ActiveTabChangeEvent) => {
        this.#tabLabel = event.label;
        this.publish();
    };

    publish() {
        if (this.#pathname === null || this.#match === null) {
            return;
        }

        const entries = findBreadcrumbEntries(this.host.navigationEntries, {
            pathname: this.#pathname,
            path: currentInterfacePath(this.#pathname),
            match: this.#match,
            objectName: this.#objectName,
            tabLabel: this.#tabLabel,
        });

        if (!sameEntries(this.provider.value, entries)) {
            this.provider.setValue(entries);
        }
    }

    hostConnected() {
        this.#abortController?.abort();
        const { signal } = (this.#abortController = new AbortController());
        window.addEventListener(ActiveTabChangeEvent.eventName, this.activeTabListener, { signal });
        window.addEventListener(PageDetailsUpdate.eventName, this.pageDetailsListener, { signal });
    }

    hostDisconnected() {
        this.#abortController?.abort();
        this.#abortController = null;
    }

    hostUpdated() {
        if (this.host.pathname !== this.#pathname) {
            const match = matchRoute(currentInterfacePath(this.host.pathname), ROUTES);

            if (!sameRouteMatch(this.#match, match)) {
                this.#objectName = null;
                this.#tabLabel = null;
            }

            this.#pathname = this.host.pathname;
            this.#match = match;
        }

        this.publish();
    }
}
