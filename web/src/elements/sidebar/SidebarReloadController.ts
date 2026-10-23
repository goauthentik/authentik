import { type SidebarExpansionState } from "./expansion";
import * as SidebarExpansion from "./expansion.ts";
import { type Sidebar } from "./Sidebar";

import { ReactiveController } from "lit";

type SidebarEntry = [string, boolean | undefined];

export class SidebarReloadController implements ReactiveController {
    protected persisted: SidebarExpansionState = {};

    constructor(protected host: Sidebar) { }

    hostConnected() {
        const persisted = SidebarExpansion.readState() ?? {};
        this.host.expanded = new Map<string, boolean>(Object.entries(persisted));
        this.host.requestUpdate();
    }

    writeState() {
        const persisted = Array.from(this.host.expanded.entries()).reduce(
            (acc: SidebarExpansionState, [key, value]: SidebarEntry): SidebarExpansionState =>
                typeof value === "undefined" ? acc : { ...acc, [key]: value },
            {},
        );

        SidebarExpansion.writeState(persisted);
    }

    hostUpdated() {
        this.writeState();
    }

    hostDisconnected() {
        this.writeState();
    }
}
